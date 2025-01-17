from django.urls import path
from .consumers import ChatConsumer, ChatsConsumer


websocket_urlpatterns = [
    path('ws/chat/<int:id>/', ChatConsumer.as_asgi()), 
    path('ws/chats/', ChatsConsumer.as_asgi()), 


]





