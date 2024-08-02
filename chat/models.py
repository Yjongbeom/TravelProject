from django.db import models

class User(models.Model):
    travel_user_id = models.IntegerField(default=0)
    jwt_token = models.TextField(blank=True, null=True)
    jwt_refresh_token = models.TextField(blank=True, null=True)

class ChatRoom(models.Model):
    id = models.BigAutoField(primary_key=True)
    room_name = models.CharField(max_length=255, default='Default')
    users = models.ManyToManyField(User, related_name='chat_rooms')

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
