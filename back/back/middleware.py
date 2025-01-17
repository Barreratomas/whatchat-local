import jwt
from django.conf import settings
from django.http import JsonResponse
from django.urls import resolve

def authenticate_request(get_response):
    def middleware(request):
        auth_header = request.headers.get('Authorization')

        # Obtener la URL de la solicitud
        current_url = resolve(request.path_info).url_name

        # Permitir el acceso a las rutas 'login' y 'register' sin token
        if current_url in ['login', 'register']:
            return get_response(request)

        # Verificar el token en el encabezado Authorization
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Decodificar el token para comprobar su validez
                payload = jwt.decode(token, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
                request.user_sub = payload.get('sub')  # Asignar el 'sub' al request
                
                return get_response(request)
            except jwt.InvalidTokenError:
                return JsonResponse({"detail": "Token inválido. Debes iniciar sesión nuevamente."}, status=401)

        # Si no hay token, el usuario no está autenticado
        return JsonResponse({"detail": "No se encontró el token de acceso. Debes iniciar sesión."}, status=401)

    return middleware