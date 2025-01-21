from django.http import JsonResponse
from rest_framework import serializers
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404

import json


from .models import User, FriendRequest, Friend
from .serializers import UserSerializer, FriendRequestSerializer
from chats.models import Chat


# mostrar usuario
@require_http_methods(["GET"])
def index(request):
    try:
        search = request.GET.get("search", "")
        users = User.objects.filter(Q(username__icontains=search))

        serializer = UserSerializer(users, many=True)

        response_data = {
            "code": 200,
            "message": "Usuarios obtenidos correctamente",
            "status": "success",
            "data": {"users": serializer.data},
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno en users index",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


# mostrar informacion del usuario logueado
@require_http_methods(["GET"])
def me(request):
    try:
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        serializer = UserSerializer(user)

        response_data = {
            "code": 200,
            "message": "Usuario obtenido correctamente",
            "status": "success",
            "data": {"users": serializer.data},
        }
        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno en users index",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)













# actualizar usuario
@csrf_exempt
@require_http_methods(["PUT"])
def update(request):
    try:
        from_user_email = request.user_sub
        user = get_object_or_404(User, email=from_user_email)

        if user:
            data = json.loads(request.body)

            # Pasamos el ID del usuario actual al contexto del serializer
            serializer = UserSerializer(
                user, data=data, partial=True, context={"user_id": user.id}
            )  # partial=True permite actualizar solo algunos campos

            if serializer.is_valid():

                with transaction.atomic():
                    serializer.save()
                response_data = {
                    "code": 200,
                    "message": "Usuario actualizado correctamente",
                    "status": "success",
                    "data": serializer.data,
                }
                return JsonResponse(response_data, status=200)
            else:
                response_data = {
                    "code": 400,
                    "message": "Datos no válidos",
                    "status": "error",
                    "errors": serializer.errors,
                }
                return JsonResponse(response_data, status=400)

        else:
            response_data = {
                "code": 404,
                "message": "Usuario no encontrado",
                "status": "error",
            }
            return JsonResponse(response_data, status=404)
    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno en users update",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


# guardar usuario
@csrf_exempt
@require_http_methods(["POST"])
def store(request):
    try:
        data = json.loads(request.body)

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()

            response_data = {
                "code": 201,
                "message": "Usuario creado correctamente",
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
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno en users store",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


# eliminar usuario
@csrf_exempt
@require_http_methods(["DELETE"])
def destroy(request, id):
    try:
        user = User.objects.get(id=id)
        if user:
            with transaction.atomic():

                user.delete()
            response_data = {
                "code": 204,
                "message": "Usuario eliminado correctamente",
                "status": "success",
            }

            return JsonResponse(response_data, status=204)
        else:
            response_data = {
                "code": 404,
                "message": "Usuario no encontrado",
                "status": "error",
            }
            return JsonResponse(response_data, status=404)

    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno en users destroy",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)


#  enviar solicitud de amistad
@csrf_exempt
@require_http_methods(["POST"])
def send_friend_request(request):
    try:
        body = json.loads(request.body)
        from_user_email = request.user_sub
        to_username = body.get("username")

        if not from_user_email:
            return JsonResponse({"error": "Usuario no autenticado."}, status=401)

        if not to_username:
            return JsonResponse(
                {"error": "Username del destinatario no proporcionado"}, status=400
            )

        # Validar el usuario origen
        from_user = get_object_or_404(User, email=from_user_email)

        # Validar el usuario destino
        try:
            to_user = get_object_or_404(User, username=to_username)
        except Http404:
            return JsonResponse({"error": ("No se encontró un usuario con ese nombre de usuario.")}, status=404)

        # Verificar si ya existe una solicitud de amistad rechazada o revocada
        existing_request = FriendRequest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user),
            status__in=["rejected", "revoked"]
        ).first()

        if existing_request:
            # Actualizar el estado de la solicitud a 'pending'
            existing_request.status = "pending"
                # Asegurarse de que los roles estén correctos
            if existing_request.from_user != from_user or existing_request.to_user != to_user:
                existing_request.from_user = from_user
                existing_request.to_user = to_user
                
            existing_request.save()
            return JsonResponse(
                {"success": "Solicitud de amistad actualizada a pendiente."},
                status=200,
            )

        # Preparar los datos para el serializador
        data = {
            "from_user": from_user.id,
            "to_user": to_user.id,
        }

        # Validar los datos con el serializador
        serializer = FriendRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Si pasa las validaciones, crear la solicitud
        with transaction.atomic():

            friend_request = serializer.save()

        return JsonResponse({"success": "Solicitud de amistad enviada."}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Cuerpo de la solicitud inválido"}, status=400)
    
    except serializers.ValidationError as e:
        # Procesar errores para que no aparezcan como 'non_field_errors'
        errors = e.detail
        formatted_errors = {}
        for key, value in errors.items():
            if key == "non_field_errors":
                formatted_errors["error"] = value[0]
            else:
                formatted_errors[key] = value

        return JsonResponse(formatted_errors, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def accept_friend_request(request, id):
    from_user_email = request.user_sub
    user = get_object_or_404(User, email=from_user_email)

    friend_request = get_object_or_404(FriendRequest, id=id)

    serializer = FriendRequestSerializer()
    try:
        # Validar aceptación con el serializer
        serializer.validate_acceptance(user, id)
    except serializers.ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Aceptar la solicitud y agregar a los amigos
    with transaction.atomic():

        friend_request.accept()

    # Crear el chat entre los usuarios si no existe
    chat_exists = Chat.objects.filter(
        Q(user1=friend_request.from_user, user2=friend_request.to_user)
        | Q(user1=friend_request.to_user, user2=friend_request.from_user)
    ).exists()

    if not chat_exists:
        with transaction.atomic():

            Chat.objects.create(
                user1=friend_request.from_user, user2=friend_request.to_user
            )

    return JsonResponse({"message": "Solicitud de amistad aceptada."}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def reject_friend_request(request, id):
    friend_request = get_object_or_404(FriendRequest, id=id)
    print("respuesta de request ", friend_request)
    # Verificar si la solicitud está pendiente
    if friend_request.status != "pending":
        return JsonResponse({"error": "La solicitud no está pendiente."}, status=400)

    # Rechazar la solicitud
    with transaction.atomic():

        friend_request.reject()

    return JsonResponse({"message": "Solicitud de amistad rechazada."}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def view_pending_requests(request):
    from_user_email = request.user_sub
    user = get_object_or_404(User, email=from_user_email)

    # Intentar obtener solicitudes con status 'pending'
    pending_requests = FriendRequest.objects.filter(to_user=user, status="pending")

    if not pending_requests:
        print(
            f"No se encontraron solicitudes pendientes para el usuario: {user.username}"
        )

    requests_data = [
        {"id": req.id, "from_user": req.from_user.username} for req in pending_requests
    ]

    return JsonResponse({"pending_requests": requests_data}, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def view_friends(request):
    from_user_email = request.user_sub
    user = get_object_or_404(User, email=from_user_email)

    friends = Friend.objects.filter(user=user)
    friends_data = []
    for friend in friends:
        
        # Buscar el chat asociado entre el usuario y el amigo
        chat = Chat.objects.filter(
            Q(user1=user, user2=friend.friend) | Q(user1=friend.friend, user2=user)
        ).first()
        
        # Crear la estructura de datos para el amigo
        friend_data = {
            "id": friend.id,
            "username": friend.friend.username,
            "user_id": friend.friend.id,
            "blocked": friend.blocked,
            "chat_id": chat.id if chat else None,  
        }
        friends_data.append(friend_data)
    return JsonResponse({"friends": friends_data}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def remove_friend(request):
    try:
        from_user_email = request.user_sub

        data = json.loads(request.body)
        to_user_id = data.get("to_user_id")
        print(to_user_id)

        if not to_user_id:
            return JsonResponse(
                {"success": False, "message": "Error al recibir al usuario."},
                status=400,
            )

        from_user = get_object_or_404(User, email=from_user_email)
        to_user = get_object_or_404(User, id=to_user_id)

        # Buscar relación de amistad
        friend_relation = Friend.objects.filter(user=from_user, friend=to_user).first()
        if friend_relation:
            with transaction.atomic():

                friend_relation.delete()
                # Eliminar relación inversa
                Friend.objects.filter(user=to_user, friend=from_user).delete()

            # Revocar solicitud de amistad si existe
            friend_request = FriendRequest.objects.filter(
                Q(from_user=from_user, to_user=to_user, status="accepted")
                | Q(from_user=to_user, to_user=from_user, status="accepted")
            ).first()
            if friend_request:
                friend_request.status = "revoked"
                with transaction.atomic():

                    friend_request.save()

            return JsonResponse(
                {"success": True, "message": "Amigo eliminado correctamente"}
            )

        return JsonResponse(
            {"success": False, "message": "No se encontró relacion de amistad"},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def block_friend(request):
    try:
        from_user_email = request.user_sub
        data = json.loads(request.body)
        to_user_id = data.get("to_user_id")

        if not to_user_id:
            return JsonResponse(
                {"success": False, "message": "Error al recibir al usuario."},
                status=400,
            )

        # Obtener los usuarios
        from_user = get_object_or_404(User, email=from_user_email)
        to_user = get_object_or_404(User, id=to_user_id)

        # Buscar la relación de amistad y bloquearla
        friend_relation = Friend.objects.filter(user=from_user, friend=to_user).first()
        if friend_relation:
            friend_relation.blocked = True
            with transaction.atomic():

                friend_relation.save()
            return JsonResponse(
                {"success": True, "message": "Friend blocked successfully."}
            )

        return JsonResponse(
            {"success": False, "message": "No existe relacion de amistad."}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def unblock_friend(request):
    try:
        from_user_email = request.user_sub
        data = json.loads(request.body)
        to_user_id = data.get("to_user_id")

        if not to_user_id:
            return JsonResponse(
                {"success": False, "message": "Error al recibir al usuario."},
                status=400,
            )

        # Obtener los usuarios
        from_user = get_object_or_404(User, email=from_user_email)
        to_user = get_object_or_404(User, id=to_user_id)

        # Desbloquear relación de amistad
        friend_relation = Friend.objects.filter(user=from_user, friend=to_user).first()
        if friend_relation and friend_relation.blocked:
            friend_relation.blocked = False
            with transaction.atomic():

                friend_relation.save()
            return JsonResponse(
                {"success": True, "message": "Friend unblocked successfully."}
            )

        return JsonResponse(
            {"success": False, "message": "El usuario no está bloqueado."}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
