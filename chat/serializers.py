from rest_framework import serializers
from .models import ChatRoom, User, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'travel_user_id']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"

class ChatRoomSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    latest_message_timestamp = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    users = UserSerializer(many=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'room_name', 'users', 'latest_message', 'latest_message_timestamp', 'messages']

    def get_latest_message(self, obj):
        latest_msg = obj.messages.order_by('-timestamp').first()
        if latest_msg:
            return latest_msg.text
        return None

    def get_latest_message_timestamp(self, obj):
        latest_msg = obj.messages.order_by('-timestamp').first()
        if latest_msg:
            return latest_msg.timestamp.isoformat()
        return None

    def create(self, validated_data):
        users_data = validated_data.pop('users')
        room = ChatRoom.objects.create(**validated_data)
        for user_data in users_data:
            user, created = User.objects.get_or_create(travel_user_id=user_data['travel_user_id'])
            room.users.add(user)
        return room

    def update(self, instance, validated_data):
        users_data = validated_data.pop('users', None)
        instance.room_name = validated_data.get('room_name', instance.room_name)
        instance.save()

        if users_data:
            instance.users.clear()
            for user_data in users_data:
                user, created = User.objects.get_or_create(travel_user_id=user_data['travel_user_id'])
                instance.users.add(user)

        return instance

