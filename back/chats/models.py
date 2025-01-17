from django.db import models
from users.models import User

class Chat(models.Model):
    user1 = models.ForeignKey(User, related_name="chat_user1", on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name="chat_user2", on_delete=models.CASCADE)
    
    # Campos para indicar si el chat fue eliminado por alguno de los usuarios
    deleted_by_user1 = models.BooleanField(default=False)
    deleted_by_user2 = models.BooleanField(default=False)

    def __str__(self):
        return f"Chat entre {self.user1.username} y {self.user2.username}"

    class Meta:
        unique_together = ('user1', 'user2')
