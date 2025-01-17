from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db.models import Q
def validate_password_strength(password):
    """
    Valida que la contraseña contenga al menos una letra mayúscula
    y un carácter especial.
    """
    if not any(char.isupper() for char in password):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
    if not any(char in "!.-_?|" for char in password):
        raise ValidationError("La contraseña debe contener al menos un carácter especial.")
    return password

class User(models.Model):
    username = models.CharField(
        max_length=25,
        unique=True,  # Hace que el nombre de usuario sea único
    )
    email = models.EmailField(unique=True)  # Asegúrate de que el correo electrónico sea único
    password = models.CharField(
        max_length=128,  # Máxima longitud para la contraseña
        validators=[
            MinLengthValidator(7),  # Valida un mínimo de 7 caracteres
            validate_password_strength,  # Validador personalizado para mayúsculas y caracteres especiales
        ],
    )

    def __str__(self):
        return self.username


class Friend(models.Model):
    user = models.ForeignKey('User', related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey('User', related_name='friends_with', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    blocked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('revoked', 'Revoked'),

    )

    
    from_user = models.ForeignKey('User',related_name="friend_requests_sent", on_delete=models.CASCADE)
    to_user = models.ForeignKey('User',related_name="friend_requests_received", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
   
        
    
    def save(self, *args, **kwargs):
        if self.status == 'pending':  # Solo valida nuevas solicitudes
            existing_request = FriendRequest.objects.filter(
                from_user=self.from_user, 
                to_user=self.to_user
            ).exclude(status__in=['rejected', 'revoked']).exists()
            if existing_request:
                raise ValidationError("Ya existe una solicitud de amistad pendiente o aceptada.")
        super().save(*args, **kwargs)
    
        
        
    def accept(self):

        """Aceptar la solicitud de amistad."""
        if self.status != 'pending':
            raise ValidationError("Esta solicitud ya fue procesada.")
        self.status = 'accepted'
        self.save()
        
        # Eliminar solicitudes duplicadas
        existing_request = FriendRequest.objects.filter(
            Q(from_user=self.to_user, to_user=self.from_user) | Q(from_user=self.from_user, to_user=self.to_user)
        ).exclude(id=self.id).exclude(status__in=['rejected', 'revoked']).first()

        if existing_request:
            # Eliminar la solicitud duplicada
            existing_request.status = 'revoked'
            existing_request.save()
            
        # Crear la relación de amistad
        Friend.objects.create(user=self.from_user, friend=self.to_user)
        Friend.objects.create(user=self.to_user, friend=self.from_user)
        
 
            
    def revoke(self):
        """Revocar la solicitud de amistad."""
        if self.status != 'pending':
            raise ValidationError("Solo se pueden revocar solicitudes pendientes.")
        self.status = 'revoked'
        self.save()
        
    def reject(self):
        """Rechazar la solicitud de amistad."""
        if self.status != 'pending':
            raise ValidationError("Esta solicitud ya fue procesada.")
        self.status = 'rejected'
        self.save()
         
        
        
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


    