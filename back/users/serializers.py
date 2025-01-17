from rest_framework import serializers
from .models import User, FriendRequest, Friend
from django.db.models import Q
from django.contrib.auth.hashers import make_password



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # La contraseña solo se puede escribir, no leer.
        }

    def validate_username(self, value):
        user_id = self.context.get('user_id', None)
        if User.objects.filter(username=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        if password:
            validated_data['password'] = make_password(password) 
        user = super().create(validated_data)

        return user

            
class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['from_user', 'to_user', 'created_at']

            
    def validate(self, data):

        from_user = data.get('from_user')
        to_user = data.get('to_user')
        print(from_user , to_user )
        if from_user == to_user:
            raise serializers.ValidationError("No podes enviarte una solicitud de amistad a vos mismo.")

        # Verificar si ya existe una solicitud pendiente o aceptada (sin incluir las rechazadas o revocadas)
        existing_request = FriendRequest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).exclude(status__in=['rejected', 'revoked']).exists()
        print(existing_request)
        if existing_request:
            raise serializers.ValidationError("No fue posible enviar la solicitud de amistad.")


        if Friend.objects.filter(
            (Q(user=from_user) & Q(friend=to_user)) |
            (Q(user=to_user) & Q(friend=from_user))
        ).exists():
            raise serializers.ValidationError("Ya son amigos.")

        return data
    
                
    def validate_acceptance(self, user, request_id):
        """
        Validar que el usuario es el destinatario de la solicitud y que esta sea pendiente.
        """
        friend_request = self.get_instance(request_id)

        # Verificar que el usuario que acepta la solicitud sea el 'to_user'
        if friend_request.to_user != user:
            raise serializers.ValidationError("No tienes permiso para aceptar esta solicitud.")

        # Verificar si la solicitud está pendiente
        if friend_request.status != 'pending':
            raise serializers.ValidationError("La solicitud no está pendiente.")
        
        return friend_request         

    def get_instance(self, request_id):
        """
        Obtener la instancia de la solicitud de amistad por su id.
        """
        return FriendRequest.objects.get(id=request_id)     
        
        
        