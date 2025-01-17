import jwt
from django.conf import settings
import requests  
from django.shortcuts import get_object_or_404
from django.db import transaction


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password

from users.models import User
from users.serializers import UserSerializer

def create_access_token(email: str):
    payload = {
        "sub": email,  
    }
    return jwt.encode(payload, settings.SIMPLE_JWT['SIGNING_KEY'], algorithm=settings.SIMPLE_JWT['ALGORITHM'])



def inicio(request):
    return JsonResponse({"message": "Bienvenido a la API"})




@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    try:
        data = json.loads(request.body)
        serializer = UserSerializer(data=data)

        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            print("guarda")

            return JsonResponse(serializer.data, status=201)
        return JsonResponse({"errors": serializer.errors}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido."}, status=400)
    except Exception as e:
        return JsonResponse({"detail": f"Error de registro: {str(e)}"}, status=500)




@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    data = json.loads(request.body)
    google_token = data.get('token')
    email = data.get('email')
    password = data.get('password')

    
    if google_token:
        try:
            google_verify_url = f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={google_token}'
            response = requests.get(google_verify_url)
            
            if response.status_code != 200:
                return JsonResponse({"detail": "Token de Google inválido o expirado"}, status=400)

            google_data = response.json()
            print(google_data)
            if 'email' not in google_data:
                return JsonResponse({"detail": "Token de Google inválido: no se pudo extraer el email"}, status=400)
            email = google_data['email']  # Usamos el email proporcionado por Google

            user, created = User.objects.get_or_create(email=email)

            if created:
                # Si el usuario es nuevo, puedes agregar aquí el código para crear un nuevo usuario
                user.save()
            access_token = create_access_token(user.email)

            return JsonResponse({"message": "Inicio de sesión exitoso", "token": access_token})

        except requests.exceptions.RequestException as e:
            return JsonResponse({"detail": f"Error al verificar el token: {str(e)}"}, status=500)
    

    try:
        user = User.objects.get(email=email)  

    except User.DoesNotExist:
        return JsonResponse({"detail": "Credenciales incorrectas"}, status=400)


    if not check_password(password, user.password):
        return JsonResponse({"detail": "Credenciales incorrectas"}, status=400)
    access_token = create_access_token(user.email)   
    return JsonResponse({"message": "Inicio de sesión exitoso", "token": access_token})


@csrf_exempt
@require_http_methods(["GET"])
def getTokenByUserId(request,id):
    try:
        user = get_object_or_404(User, id=id)
        access_token = create_access_token(user.email)

        response_data = {
            "code": 200,
            "status": "success",
            "access_token": access_token,
        }
        return JsonResponse(response_data, status=200)
    except Exception as e:
        response_data = {
            "code": 500,
            "message": "Ocurrio un error interno al obtener con el token del usuario",
            "status": "error",
            "error": str(e),
        }
        return JsonResponse(response_data, status=500)    


# usar para cuando se haga una bd de tokens para la centralizacion de tokens
@require_http_methods(["POST"])
def logout(request):
    """Elimina la cookie del token de acceso."""
    response = JsonResponse({"message": "Logout exitoso"})
    response.delete_cookie('access_token')  # Elimina la cookie que contiene el token
    return response



