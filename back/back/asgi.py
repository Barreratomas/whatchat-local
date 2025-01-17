import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
import chats.routing 


# Establecer la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back.settings')

# Definir el enrutamiento de canales
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": 
        URLRouter(
            chats.routing.websocket_urlpatterns
        
    ),
})
