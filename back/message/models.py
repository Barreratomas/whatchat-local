from django.db import models


from users.models import User
from chats.models import Chat


class Message(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(Chat, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)  

    def __str__(self):
        return f"{self.user.username}: {self.content}"