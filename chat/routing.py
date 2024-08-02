from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:room_id>/', consumers.ChatConsumer.as_asgi()),
    # path('ws/friend/<int:travel_user_id>/', consumers.FriendConsumer.as_asgi()),
]