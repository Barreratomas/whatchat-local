from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from django.db import transaction
from django.db.models import Q, Subquery, OuterRef, Max

from django.db import models
import json
from django.core.exceptions import ObjectDoesNotExist

from .models import Chat
from users.models import User
from users.models import Friend
from message.models import Message
from .serializers import ChatSerializer
from message.serializers import MessageSerializer


@csrf_exempt
@require_http_methods(["GET"])
def index(request):
    try:
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        # Obtener los chats donde el usuario no haya eliminado el chat
        chats = Chat.objects.filter(
            (models.Q(user1=user) & ~models.Q(deleted_by_user1=True))
            | (models.Q(user2=user) & ~models.Q(deleted_by_user2=True))
        )

        # Subconsulta para obtener el timestamp del último mensaje de cada chat
        last_message_timestamp = (
            Message.objects.filter(chat_room=OuterRef("id"))
            .order_by("-timestamp")
            .values("timestamp")[:1]
        )

        # Añadir anotación para ordenar los chats por el último mensaje
        chats = chats.annotate(
            last_message_time=Subquery(last_message_timestamp)
        ).order_by("-last_message_time")

        # Construir la respuesta manualmente
        chat_data = []
        for chat in chats:
            # Obtener el otro usuario
            other_user = chat.user2 if chat.user1 == user else chat.user1

            # Obtener el último mensaje del chat
            last_message = (
                Message.objects.filter(chat_room=chat).order_by("-timestamp").first()
            )

            # Contar los mensajes no vistos para el usuario actual
            unseen_messages_count = Message.objects.filter(
                chat_room=chat, seen=False, user=other_user
            ).count()

            chat_data.append(
                {
                    "id": chat.id,
                    "other_user": other_user.username,
                    "last_message": {
                        "content": (
                            last_message.content
                            if last_message
                            else "No hay mensajes aún"
                        ),
                        "seen": last_message.seen if last_message else False,
                    },
                    "unseen_messages_count": unseen_messages_count,
                }
            )

        response_data = {
            "code": 200,
            "message": "Chats obtenidos correctamente",
            "status": "success",
            "data": {"chats": chat_data},
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        # Agregar detalles del error para depuración
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al obtener los chats",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def filter(request):
    try:
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        # Obtener el filtro del cuerpo de la solicitud
        data = json.loads(request.body)
        username_filter = data.get("username", None)

        print(f"Filtro recibido: {username_filter}")  # Verificar el filtro recibido

        chats = []  # Lista de chats encontrados

        if username_filter:
            print(f"Filtro de usuario recibido: {username_filter}")
            # Buscar el usuario con el nombre proporcionado
            try:
                other_user = User.objects.get(username=username_filter)
                print(f"Usuario encontrado: {other_user.username}")
            except User.DoesNotExist:
                other_user = None
                print("Usuario no encontrado.")

            if other_user:
                # Si el usuario existe, buscar el chat
                chats = Chat.objects.filter(
                    (Q(user1=user) & Q(user2=other_user))
                    | (Q(user2=user) & Q(user1=other_user))
                )
                print(f"Chats encontrados: {len(chats)}")

            if not chats:
                # Si no se encontró el chat, buscar en los amigos
                friends = Friend.objects.filter(user=user)
                friend_users = friends.values_list("friend__username", flat=True)

                print(f"Amigos encontrados: {len(friend_users)}")
                print(f"Amigos: {friend_users}")  # Ver la lista de amigos

                # Buscar los amigos que coinciden con el filtro
                matching_friends = [
                    friend for friend in friend_users if username_filter in friend
                ]

                print(f"Amigos coincidentes: {matching_friends}")

                # Si hay amigos que coinciden, devolverlos en la respuesta
                if matching_friends:

                    chat_data = []
                    for friend in matching_friends:
                        chat_data.append(
                            {
                                "id": friend,  # Usamos el nombre del amigo como el ID en este caso
                                "other_user": friend,
                                "last_message": {
                                    "content": "No hay mensajes aún",  # Como no hay mensajes en este contexto, se coloca un mensaje predeterminado
                                    "seen": False,  # Suponemos que aún no se ha visto el mensaje
                                },
                            }
                        )

                    response_data = {
                        "code": 200,
                        "message": "Amigos encontrados",
                        "status": "success",
                        "data": {"chats": chat_data},
                    }
                else:
                    # Si no se encuentran amigos que coincidan, responde con un mensaje adecuado
                    response_data = {
                        "code": 404,
                        "message": "No se encontraron amigos que coincidan con el filtro",
                        "status": "error",
                    }

                return JsonResponse(response_data, status=200)

        # Si se encontraron chats, continuar con la lógica actual
        print(
            f"Chats antes de ordenar: {len(chats)}"
        )  # Ver cuántos chats tenemos antes de la ordenación

        # Subconsulta para obtener el timestamp del último mensaje de cada chat
        last_message_timestamp = (
            Message.objects.filter(chat_room=OuterRef("id"))
            .order_by("-timestamp")
            .values("timestamp")[:1]
        )

        # Añadir anotación para ordenar los chats por el último mensaje
        chats = (
            Chat.objects.filter(id__in=[chat.id for chat in chats])
            .annotate(last_message_time=Subquery(last_message_timestamp))
            .order_by("-last_message_time")
        )

        print(
            f"Chats ordenados por último mensaje: {len(chats)}"
        )  # Ver cuántos chats se han ordenado

        # Construir la respuesta manualmente
        chat_data = []
        for chat in chats:
            # Obtener el otro usuario
            other_user = chat.user2 if chat.user1 == user else chat.user1
            print(f"Otro usuario en el chat: {other_user.username}")

            # Obtener el último mensaje del chat
            last_message = (
                Message.objects.filter(chat_room=chat).order_by("-timestamp").first()
            )
            chat_data.append(
                {
                    "id": chat.id,
                    "other_user": other_user.username,
                    "last_message": {
                        "content": (
                            last_message.content
                            if last_message
                            else "No hay mensajes aún"
                        ),
                        "seen": last_message.seen if last_message else False,
                    },
                }
            )

        response_data = {
            "code": 200,
            "message": "Chats filtrados correctamente",
            "status": "success",
            "data": {"chats": chat_data},
        }

        print(
            f"Respuesta enviada: {len(chat_data)} chats encontrados"
        )  # Ver cuántos chats se envían en la respuesta

        return JsonResponse(response_data, status=200)

    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")  # Ver el error
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al filtrar los chats",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def chat(request, id):
    try:
        from_user_email = request.user_sub

        user = get_object_or_404(User, email=from_user_email)

        # Validar si el chat existe
        try:
            chat = Chat.objects.get(id=id)
        except Chat.DoesNotExist:
            return JsonResponse(
                {"code": 404, "message": "Chat no encontrado", "status": "error"},
                status=404,
            )

        # Validar si el usuario pertenece al chat
        if chat.user1 != user and chat.user2 != user:
            return JsonResponse(
                {"code": 403, "message": "Acceso denegado al chat", "status": "error"},
                status=403,
            )

        # Obtener los mensajes del chat
        mensajes = Message.objects.filter(chat_room=chat).order_by("timestamp")

        # Marcar como vistos los mensajes no vistos por el usuario
        mensajes_no_vistos = mensajes.filter(seen=False).exclude(user=user)
        mensajes_no_vistos.update(seen=True)

        # Serializar los mensajes
        serializer = MessageSerializer(mensajes, many=True)

        # Respuesta exitosa
        response_data = {
            "code": 200,
            "message": "Mensajes obtenidos correctamente",
            "status": "success",
            "data": {"chat_id": chat.id, "messages": serializer.data},
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        # Manejo de errores
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al obtener el chat",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


def get_chat(user1_id, user2_id):
    try:

        # Verificar que los usuarios existen
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)

    except User.DoesNotExist:
        raise ValueError(
            "Uno de los usuarios no existe"
        )  # Lanzar una excepción personalizada

    # Buscar el chat entre los dos usuarios
    chat = Chat.objects.filter(
        (models.Q(user1_id=user1.id) & models.Q(user2_id=user2.id))
        | (models.Q(user1_id=user2.id) & models.Q(user2_id=user1.id))
    ).first()
    if chat:
        return chat
    else:
        return None

@csrf_exempt
@require_http_methods(["POST"])
def notification(request):
    try:
        # Obtener el usuario actual a partir del token
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        # Obtener los datos del cuerpo de la solicitud (id del otro usuario)
        data = json.loads(request.body)
        other_user_id = data.get("id_other_user", None)

        if not other_user_id:
            return JsonResponse(
                {
                    "code": 400,
                    "message": "Se requiere el ID del otro usuario.",
                    "status": "error",
                },
                status=400,
            )

        # Obtener al otro usuario
        other_user = get_object_or_404(User, id=other_user_id)

        # Buscar el chat entre el usuario actual y el otro usuario utilizando la función get_chat
        chat = get_chat(user.id, other_user.id)

        if not chat:
            return JsonResponse(
                {
                    "code": 404,
                    "message": "Chat no encontrado o eliminado.",
                    "status": "error",
                },
                status=404,
            )

        # Obtener el último mensaje del chat
        last_message = Message.objects.filter(chat_room=chat).order_by('-timestamp').first()

        if not last_message:
            return JsonResponse(
                {
                    "code": 204,
                    "message": "No hay nuevos mensajes.",
                    "status": "success",
                },
                status=204,
            )

        # Construir la respuesta con los detalles del último mensaje
        response_data = {
            "code": 200,
            "message": "Nueva notificación de mensaje.",
            "status": "success",
            "data": {
                "chat_id": chat.id,
                "other_user": {
                    "id": user.id,
                    "username": user.username,
                },
                "last_message": {
                    "id": last_message.id,
                    "content": last_message.content,
                },
            },
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al procesar la notificación.",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def create(request):

    try:
        from_user_email = request.user_sub

        user1 = get_object_or_404(User, email=from_user_email)

        data = json.loads(request.body)
        username_2 = data.get("username")

        user2 = User.objects.get(username=username_2)

        chat = get_chat(user1.id, user2.id)

        if chat is None:

            chat_data = {"user1": user1.id, "user2": user2.id}

            serializer = ChatSerializer(data=chat_data)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                response_data = {
                    "code": 201,
                    "message": "Chat creado correctamente",
                    "status": "success",
                    "data": serializer.data,
                }
                return JsonResponse(response_data, status=201)
            else:
                response_data = {
                    "code": 400,
                    "message": "Datos no válidos",
                    "status": "error",
                    "errors": serializer.errors,
                }
                return JsonResponse(response_data, status=400)

        serializer = ChatSerializer(chat)
        response_data = {
            "code": 200,
            "message": "El chat ya existe",
            "status": "success",
            "data": serializer.data,
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al crear el chat",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def destroy(request, id):
    try:
        # Obtener el chat
        chat = Chat.objects.get(id=id)

        from_user_email = request.user_sub

        user = get_object_or_404(User, email=from_user_email)

        # Verificar si el usuario que realiza la eliminación es user1 o user2
        if chat.user1 == user:
            chat.deleted_by_user1 = True
        elif chat.user2 == user:
            chat.deleted_by_user2 = True
        else:
            return JsonResponse(
                {
                    "code": 403,
                    "message": "No tienes permiso para eliminar este chat",
                    "status": "error",
                },
                status=403,
            )

        # Guardar los cambios en la base de datos
        with transaction.atomic():
            chat.save()

        response_data = {
            "code": 204,
            "message": "Chat eliminado correctamente desde tu perspectiva",
            "status": "success",
        }
        return JsonResponse(response_data, status=204)

    except Chat.DoesNotExist:
        response_data = {
            "code": 404,
            "message": "Chat no encontrado",
            "status": "error",
        }
        return JsonResponse(response_data, status=404)
    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrió un error al eliminar el chat",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete(request, id):
    try:
        chat = Chat.objects.get(id=id)
        with transaction.atomic():
            chat.delete()
        return JsonResponse({"message": "ok"}, status=200)
    except Exception as e:
        return JsonResponse({"message": "error"}, status=500)
