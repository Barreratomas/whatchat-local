from rest_framework import serializers
from .models import Message
from chats.models import Chat
from users.models import Friend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

class MessageSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()  # Agregamos un campo para el username


    class Meta:
        model = Message
        fields = ['id', 'content', 'user', 'chat_room', 'timestamp', 'seen','username']


    def get_username(self, obj):
        return obj.user.username if obj.user else None

    # Validación del contenido del mensaje
    def validate_content(self, value):
        if not value.strip():  # Verifica si el contenido del mensaje está vacío
            raise serializers.ValidationError(_("El contenido del mensaje no puede estar vacío"))
        return value

    def validate(self, data):
        user = data.get('user')
        chat_room = data.get('chat_room')
        
        # Verificar que el chat existe y que el usuario está en el chat
        try:
            chat = Chat.objects.get(id=chat_room.id)
        except Chat.DoesNotExist:
            raise serializers.ValidationError(_("El chat no existe"))

        if user.id not in [chat.user1.id, chat.user2.id]:
            raise serializers.ValidationError(_("El usuario no está autorizado a enviar mensajes en este chat"))
        
        
        # Restaurar el estado del chat si estaba eliminado
        if chat.user1 == user and chat.deleted_by_user1:
            chat.deleted_by_user1 = False
            chat.save()
        elif chat.user2 == user and chat.deleted_by_user2:
            chat.deleted_by_user2 = False
            chat.save()
        
        
        # Verificar si el usuario está bloqueado
        # Caso 1: Verificar si el usuario que envía el mensaje está bloqueado por el otro usuario
        is_blocked = Friend.objects.filter(
            (Q(user=user) & Q(friend=chat.user1) & Q(blocked=True)) | 
            (Q(user=user) & Q(friend=chat.user2) & Q(blocked=True)) | 
            (Q(user=chat.user1) & Q(friend=user) & Q(blocked=True)) | 
            (Q(user=chat.user2) & Q(friend=user) & Q(blocked=True))
        ).exists()

        if is_blocked:
            raise serializers.ValidationError(_("No puedes enviar mensajes a este usuario porque te ha bloqueado o lo has bloqueado"))
        
        return data
