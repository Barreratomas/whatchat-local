from channels.generic.websocket import AsyncWebsocketConsumer
import json
import httpx
from channels.db import database_sync_to_async
from datetime import datetime, timezone
from message.models import Message
from chats.models import Chat


class ChatConsumer(AsyncWebsocketConsumer):

    async def get_current_user(self, token):
        """Obtiene los datos del usuario actual llamando a la API."""
        api_url = f"http://127.0.0.1:8000/api/users/me"  # Asegúrate de configurar API_BASE_URL
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data["data"]["users"]
                else:
                    print(f"Error al obtener el usuario: {response.status_code}")
            except Exception as e:
                print(f"Error al llamar a la API de usuario: {e}")

        return None

    @database_sync_to_async
    def get_other_user(self, room_id, current_user_id):
        """Obtiene al otro usuario del chat usando el modelo Chat."""
        try:
            chat = Chat.objects.get(id=room_id)
            if chat.user1.id == current_user_id:
                return {
                    "id": chat.user2.id,
                    "username": chat.user2.username,
                    "email": chat.user2.email,
                }
            elif chat.user2.id == current_user_id:
                return {
                    "id": chat.user1.id,
                    "username": chat.user1.username,
                    "email": chat.user1.email,
                }
            return None
        except Chat.DoesNotExist:
            print(f"No existe un chat con ID {room_id}")
            return None

    async def connect(self):
        # Lógica de conexión del WebSocket
        self.room_id = self.scope["url_route"]["kwargs"]["id"]
        self.room_group_name = f"room_{self.room_id}"
        token = self.get_token_from_query_string()
        self.token = token  # Guardar el token en una variable de instancia

        current_user = await self.get_current_user(token)
        if not current_user:
            await self.close()
            return

        # Obtener el otro usuario del chat
        other_user = await self.get_other_user(self.room_id, current_user["id"])
        if not other_user:
            print("No se pudo encontrar al otro usuario. Cerrando conexión.")
            await self.close()
            return

        # Unirse al grupo de la sala
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Obtener el historial de mensajes llamando a la API
        messages = await self.get_chat_messages(self.room_id)

        # Enviar los mensajes al frontend
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "messages": messages,
                    "other_user": other_user,
                }
            )
        )

    async def disconnect(self, close_code):
        # Dejar el grupo de la sala
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None):
        try:
            text_data_json = json.loads(text_data)

            message_type = text_data_json.get("type")

            if message_type == "delete_message":
                message_id = text_data_json.get("message_id")
                if message_id:
                    # Llamar a la API para eliminar el mensaje
                    await self.delete_message(message_id)
                    # Responder en tiempo real a todos los usuarios que el mensaje ha sido eliminado
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "message_deleted",
                            "message_id": message_id,
                        },
                    )
                else:
                    raise ValueError("Message ID is required for delete_message")

            elif message_type == "update_message":
                message_id = text_data_json.get("message_id")
                new_content = text_data_json.get("content")
                if message_id and new_content:
                    await self.update_message(message_id, new_content)
                    # Informar a los usuarios que el mensaje ha sido actualizado
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "message_updated",
                            "message_id": message_id,
                            "new_content": new_content,
                        },
                    )
                else:
                    raise ValueError(
                        "Both message_id and new_content are required for update_message"
                    )

            elif message_type == "mark_seen":
                room_id = self.room_id
                user_id = text_data_json.get("user_id")
                if user_id:
                    await self.mark_all_as_seen(room_id, user_id)
                    # Notificar a todos en el grupo del chat
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "messages_marked_seen",
                            "user_id": user_id,
                        },
                    )
                else:
                    raise ValueError("el user id es necesario para mark_seen")

            elif message_type == "send_message":
                message = text_data_json.get("message")
                user_id = text_data_json.get("user_id")
                username = text_data_json.get("username")

                if message and user_id and username:
                    # Llamar al API para guardar el mensaje
                    message_object = await self.save_message(message, user_id, username)

                    # Enviar el mensaje al grupo en tiempo real
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "message": message,
                            "user_id": user_id,
                            "username": username,
                            "seen": False,
                            "message_id": message_object.get("data", {}).get("id"),
                        },
                    )
                else:
                    raise ValueError(
                        "Message, user_id, and username are required for send_message"
                    )

        except Exception as e:
            print(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def update_message(self, message_id, new_content):
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://127.0.0.1:8000/api/messages/editar/{message_id}",
                json={"new_content": new_content},
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
            )
        if response.status_code == 200:

            return response.json()
        else:
            raise Exception(f"Error al actualizar el mensaje: {response.json()}")

    async def message_updated(self, event):
        message_id = event["message_id"]
        new_content = event["new_content"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_updated",
                    "message_id": message_id,
                    "new_content": new_content,
                }
            )
        )

    async def messages_marked_seen(self, event):
        user_id = event["user_id"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "messages_marked_seen",
                    "user_id": user_id,
                }
            )
        )

    async def delete_message(self, message_id):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://127.0.0.1:8000/api/messages/eliminar/{message_id}",
                headers={
                    "Authorization": f"Bearer {self.token}",  # Usar el token de autenticación
                },
            )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error al eliminar el mensaje: {response.json()}")

    async def message_deleted(self, event):
        message_id = event["message_id"]
        # Solo envia el evento sin datos adicionales si no deseas enviar el message_id
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_deleted",  # Solo el tipo del evento
                    "message_id": message_id,
                }
            )
        )

    async def chat_message(self, event):
        message = event["message"]
        user_id = event["user_id"]
        username = event["username"]
        seen = event["seen"]
        message_id = event["message_id"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "messages": [
                        {
                            "content": message,
                            "username": username,
                            "user": user_id,
                            "timestamp": datetime.now(timezone.utc).strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "seen": seen,
                            "id": message_id,
                        }
                    ],
                }
            )
        )

    @database_sync_to_async
    def mark_all_as_seen(self, room_id, user_id):

        messages = Message.objects.filter(chat_room_id=room_id, seen=0).exclude(
            user_id=user_id
        )
        messages.update(seen=1)

    async def get_chat_messages(self, id):
        url = f"http://127.0.0.1:8000/api/chats/chat/{id}"
        headers = {
            "Authorization": f"Bearer {self.token}",  # Usar el token de autenticación
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            # Si la respuesta es exitosa, extraemos los mensajes
            data = response.json()
            return data["data"]["messages"]  # Devuelve la lista de mensajes

        else:
            # Si ocurre un error, maneja el caso aquí
            return []

    # Método para extraer el token del query string
    def get_token_from_query_string(self):
        query_string = self.scope["query_string"].decode()
        token = None
        for param in query_string.split("&"):
            key, value = param.split("=")
            if key == "token":
                token = value
                break
        return token

    async def save_message(self, message, user_id, username):

        # Realizar la solicitud POST para crear el mensaje
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/api/messages/crear",
                json={
                    "content": message,
                    "chat_room": self.room_id,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",  # Usar el token de autenticación
                },
            )

        if response.status_code == 201:
            return response.json()  # Devuelve el mensaje guardado con el ID
        else:
            # Maneja el error si la creación del mensaje falla
            raise Exception(f"Error al guardar el mensaje: {response.json()}")


class ChatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Token de autenticación del query string
        token = self.get_token_from_query_string()
        self.token = token  # Guardar el token en una variable de instancia
        self.user_id = self.scope["query_string"].decode().split("user_id=")[1]

        # Usar el user_id para generar un nombre de grupo único y válido
        self.room_group_name = f"chat_list_group_{self.user_id}"

        # Unirse al grupo de chats del usuario
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Aceptar la conexión WebSocket
        await self.accept()

        # Obtener la lista de chats para el usuario basado en el token
        chats = await self.get_chat_list()

        # Enviar los chats al frontend
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_list",  # Tipo de mensaje para la lista de chats
                    "chats": chats,  # Lista de chats obtenida de la API
                }
            )
        )

    async def disconnect(self, close_code):
        # Dejar el grupo de chats
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "update_chat_list":
                user_id = text_data_json.get("user_id")
                other_user_id = text_data_json.get("other_user_id")
                notification_type = text_data_json.get("notification", "default_value")

                if user_id and other_user_id:
                    # Obtener y enviar la lista de chats actualizada
                    chats = await self.get_chat_list()
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_list",
                            "chats": chats,
                        },
                    )
                    # También enviar al otro usuario
                    other_user_token = await self.get_other_user_token(other_user_id)
                    chats = await self.get_other_chat_list(other_user_token)
                    
                    await self.channel_layer.group_send(
                        f"chat_list_group_{other_user_id}",
                        {
                            "type": "chat_list",
                            "chats": chats,
                        },
                    )
                    if notification_type == "notification":
                        notification = await self.get_notification(other_user_id)
                        await self.channel_layer.group_send(
                            f"chat_list_group_{other_user_id}",
                            {
                                "type": "notification",
                                "noti": notification,
                            },
                        )

                else:
                    raise ValueError(
                        "user_id y other_user_id son requeridos para update_chat_list"
                    )

        except Exception as e:
            print(f"Error en receive: {e}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def chat_list(self, event):
        # Este método maneja la actualización de la lista de chats para los clientes
        chats = event["chats"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_list",
                    "chats": chats, 
                }
            )
        )
        
        
    async def notification(self, event):
        notification = event["noti"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification": notification,  
                }
            )
        )
        
        
        
        
        
        
        
        
        
        
        
        

    async def get_chat_list(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/chats/",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",  # Usar el token de autenticación
                },
            )

        if response.status_code == 200:
            response_data = response.json()  # Convierte la respuesta en JSON
            return response_data["data"]["chats"]
        else:
            raise Exception(f"Error al obtener los chats: {response.json()}")

    # Método para extraer el token del query string
    def get_token_from_query_string(self):
        query_string = self.scope["query_string"].decode()
        token = None
        for param in query_string.split("&"):
            key, value = param.split("=")
            if key == "token":
                token = value
                break
        return token

    async def get_other_user_token(self, other_user):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://127.0.0.1:8000/api/getToken/{other_user}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                },
            )
        if response.status_code == 200:
            response_data = response.json()
            return response_data["access_token"]
        else:
            raise Exception(f"Error al obtener los chats: {response.json()}")

    async def get_other_chat_list(self, other_user_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/chats/",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {other_user_token}",
                },
            )

        if response.status_code == 200:
            response_data = response.json()
            return response_data["data"]["chats"]
        else:
            raise Exception(f"Error al obtener los chats: {response.json()}")

    async def get_notification(self, other_user_id):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://127.0.0.1:8000/api/chats/notification",
                json={
                    "id_other_user": other_user_id,  
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                },
            )
        if response.status_code == 200:
            response_data = response.json()  

            return response_data 
        else:
            raise Exception(f"Error al obtener la notificacion: {response.json()}")