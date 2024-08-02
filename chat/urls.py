from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomListCreateAPIView.as_view(), name='chat_rooms'),
    path('rooms/<int:pk>/', views.ChatRoomRetrieveUpdateAPIView.as_view(), name='chat_room_update'),
    path('<int:room_id>/messages/', views.MessageListAPIView.as_view(), name='chat_messages'),
]
