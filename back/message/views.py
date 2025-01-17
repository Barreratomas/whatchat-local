from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

import json

from .models import Message
from .serializers import MessageSerializer

from chats.models import Chat
from users.models import User,Friend




    

@csrf_exempt
@require_http_methods(["POST"])
def create(request):
    try:
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        data = json.loads(request.body)  

        data['user'] = user.id  

        serializer = MessageSerializer(data=data, context={"user": user})
    
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            response_data = {
                "code": 201,
                "message": "mensaje insertado correctamente",
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
    except Exception as e:
        return JsonResponse({"error":str(e)},status=500)
    
    
@csrf_exempt
@require_http_methods(["PUT"])
def update(request, id):
    try:
        # Obtener el usuario autenticado
        from_user_email = request.user_sub  # Suposición de que `user_sub` contiene el email del usuario autenticado
        user = get_object_or_404(User, email=from_user_email)

        # Verificar que el mensaje existe
        try:
            message = Message.objects.get(id=id)
        except Message.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "El mensaje no existe",
                "status": "error"
            }, status=404)

        # Verificar que el chat asociado al mensaje existe
        try:
            chat = Chat.objects.get(id=message.chat_room.id)
        except Chat.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "El chat asociado al mensaje no existe",
                "status": "error"
            }, status=404)

        # Verificar que el usuario está autorizado para actualizar mensajes en este chat
        if user.id not in [chat.user1.id, chat.user2.id]:
            return JsonResponse({
                "code": 403,
                "message": "No estás autorizado para actualizar mensajes en este chat",
                "status": "error"
            }, status=403)

        # Verificar que el usuario sea el autor del mensaje
        if message.user != user:
            return JsonResponse({
                "code": 403,
                "message": "No estás autorizado para actualizar este mensaje",
                "status": "error"
            }, status=403)

        # Obtener y validar el contenido actualizado
        data = json.loads(request.body)
        content = data.get('new_content', '').strip()

        if not content:
            return JsonResponse({
                "code": 400,
                "message": "El contenido del mensaje no puede estar vacío",
                "status": "error"
            }, status=400)

        # Actualizar el mensaje con el nuevo contenido
        message.content = content
        with transaction.atomic():
            message.save()

        return JsonResponse({
            "code": 200,
            "message": "Mensaje actualizado correctamente",
            "status": "success",
            "data": {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": str(e),
            "status": "error"
        }, status=500)
    
@csrf_exempt
@require_http_methods(["DELETE"])
def destroy(request, id):
    try:
        # Obtener el usuario autenticado a través de la solicitud
        from_user_email = request.user_sub  # Suposición de que `user_sub` contiene el email del usuario autenticado
        user = get_object_or_404(User, email=from_user_email)

        # Verificar que el mensaje existe
        try:
            message = Message.objects.get(id=id)
        except Message.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "El mensaje no existe",
                "status": "error"
            }, status=404)

        # Verificar que el chat asociado al mensaje existe
        try:
            chat = Chat.objects.get(id=message.chat_room.id)
        except Chat.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "El chat asociado al mensaje no existe",
                "status": "error"
            }, status=404)

        # Verificar que el usuario autenticado está autorizado en el chat
        if user.id not in [chat.user1.id, chat.user2.id]:
            return JsonResponse({
                "code": 403,
                "message": "No estás autorizado para realizar esta acción en este chat",
                "status": "error"
            }, status=403)

        # Verificar que el usuario sea el autor del mensaje
        if message.user != user:
            return JsonResponse({
                "code": 403,
                "message": "No estás autorizado para eliminar este mensaje",
                "status": "error"
            }, status=403)

        # Si todas las validaciones son exitosas, eliminar el mensaje
        with transaction.atomic():

            message.delete()
        return JsonResponse({
            "code": 200,
            "message": "Mensaje eliminado correctamente",
            "status": "success"
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": str(e),
            "status": "error"
        }, status=500)