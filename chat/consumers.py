import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from .models import ChatRoom, Message, User

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        participants = await self.get_participants()
        await self.send_json({
            'type': 'participants',
            'participants': participants
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        sender_id = content.get('sender_id')
        type = content.get('type', 'message')

        if type == 'message':
            await self.handle_message(content)
        elif type == 'leave':
            await self.handle_leave(content)
        elif type == 'invite':
            await self.handle_invite(content)

    async def handle_message(self, content):
        sender_id = content.get('sender_id')
        message = content.get('message')
        if not sender_id or not message:
            await self.send_json({
                'error': 'sender_id와 message는 필수입니다.'
            })
            return

        if not await self.is_participant(self.room_id, sender_id):
            await self.send_json({
                'error': '채팅방 참가자만 메시지를 보낼 수 있습니다.'
            })
            return

        timestamp = await self.save_message(self.room_id, sender_id, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'timestamp': timestamp
            }
        )

    async def handle_leave(self, content):
        sender_id = content.get('sender_id')
        user = await self.get_user_by_travel_user_id(sender_id)
        await self.remove_user_from_room(self.room_id, user)
        participants = await self.get_participants()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participants_update',
                'participants': participants
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_update',
                'room_id': self.room_id
            }
        )

        await self.send_json({
            'type': 'left',
            'room_id': self.room_id
        })

    async def handle_invite(self, content):
        travel_user_id = content.get('travel_user_id')
        user = await self.get_user_by_travel_user_id(travel_user_id)
        room = await self.get_room(self.room_id)
        await self.add_user_to_room(room, user)
        participants = await self.get_participants()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participants_update',
                'participants': participants
            }
        )

        await self.channel_layer.group_send(
            f'user_{travel_user_id}',
            {
                'type': 'room_update',
                'room_id': self.room_id
            }
        )

        logger.info(f'Sending room_update to user_{travel_user_id} with room_id {self.room_id}')

        await self.send_json({
            'type': 'invite',
            'room_id': self.room_id
        })

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        timestamp = event['timestamp']

        sender = await self.get_user_by_travel_user_id(sender_id)

        await self.send_json({
            'type': 'message',
            'message': message,
            'sender': {'travel_user_id': sender.travel_user_id},
            'timestamp': timestamp
        })

    async def participants_update(self, event):
        participants = event['participants']

        await self.send_json({
            'type': 'participants',
            'participants': participants
        })

    async def room_update(self, event):
        room_id = event['room_id']
        await self.send_json({
            'type': 'room_update',
            'room_id': room_id
        })

    @database_sync_to_async
    def save_message(self, room_id, sender_id, message_text):
        room = ChatRoom.objects.get(id=room_id)
        sender = User.objects.get(travel_user_id=sender_id)
        message = Message.objects.create(room=room, sender=sender, text=message_text)
        return message.timestamp.isoformat()

    @database_sync_to_async
    def get_user_by_travel_user_id(self, travel_user_id):
        return User.objects.get(travel_user_id=travel_user_id)

    @database_sync_to_async
    def get_room(self, room_id):
        return ChatRoom.objects.get(id=room_id)

    @database_sync_to_async
    def get_participants(self):
        room = ChatRoom.objects.get(id=self.room_id)
        participants = [{'travel_user_id': user.travel_user_id} for user in room.users.all()]
        return participants

    @database_sync_to_async
    @transaction.atomic
    def remove_user_from_room(self, room_id, user):
        room = ChatRoom.objects.get(id=room_id)
        room.users.remove(user)

    @database_sync_to_async
    @transaction.atomic
    def add_user_to_room(self, room, user):
        room.users.add(user)

    @database_sync_to_async
    def is_participant(self, room_id, travel_user_id):
        room = ChatRoom.objects.get(id=room_id)
        return room.users.filter(travel_user_id=travel_user_id).exists()


# class FriendConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         self.travel_user_id = self.scope['url_route']['kwargs']['travel_user_id']
#         self.user_group_name = f'user_{self.travel_user_id}'
#
#         await self.channel_layer.group_add(
#             self.user_group_name,
#             self.channel_name
#         )
#
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.user_group_name,
#             self.channel_name
#         )
#
#     async def receive_json(self, content):
#         type = content.get('type')
#
#         if type == 'friend_request':
#             await self.handle_friend_request(content)
#         elif type == 'friend_accept':
#             await self.handle_friend_accept(content)
#         elif type == 'friend_refuse':
#             await self.handle_friend_refuse(content)
#         elif type == 'friend_block':
#             await self.handle_friend_block(content)
#
#     async def handle_friend_request(self, content):
#         travel_user_id = content.get('travel_user_id')
#         friend_travel_user_id = content.get('friend_travel_user_id')
#
#         await self.channel_layer.group_send(
#             f'user_{travel_user_id}',
#             {
#                 'type': 'friend_request_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#                 'status': 'request'
#             }
#         )
#
#         await self.channel_layer.group_send(
#             f'user_{friend_travel_user_id}',
#             {
#                 'type': 'friend_request_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#                 'status': 'standby'
#             }
#         )
#
#     async def handle_friend_accept(self, content):
#         travel_user_id = content.get('travel_user_id')
#         friend_travel_user_id = content.get('friend_travel_user_id')
#
#         await self.channel_layer.group_send(
#             f'user_{travel_user_id}',
#             {
#                 'type': 'friend_accept_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#             }
#         )
#
#         await self.channel_layer.group_send(
#             f'user_{friend_travel_user_id}',
#             {
#                 'type': 'friend_accept_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#             }
#         )
#
#     async def handle_friend_refuse(self, content):
#         travel_user_id = content.get('travel_user_id')
#         friend_travel_user_id = content.get('friend_travel_user_id')
#
#         await self.channel_layer.group_send(
#             f'user_{travel_user_id}',
#             {
#                 'type': 'friend_refuse_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#             }
#         )
#
#         await self.channel_layer.group_send(
#             f'user_{friend_travel_user_id}',
#             {
#                 'type': 'friend_refuse_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#             }
#         )
#
#     async def handle_friend_block(self, content):
#         travel_user_id = content.get('travel_user_id')
#         friend_travel_user_id = content.get('friend_travel_user_id')
#
#         await self.channel_layer.group_send(
#             f'user_{travel_user_id}',
#             {
#                 'type': 'friend_block_message',
#                 'travel_user_id': travel_user_id,
#                 'friend_travel_user_id': friend_travel_user_id,
#             }
#         )
#     async def friend_request_message(self, event):
#         travel_user_id = event['travel_user_id']
#         friend_travel_user_id = event['friend_travel_user_id']
#         status = event['status']
#
#         await self.send_json({
#             'type': 'friend_request',
#             'travel_user_id': travel_user_id,
#             'friend_travel_user_id': friend_travel_user_id,
#             'status': status
#         })
#
#     async def friend_accept_message(self, event):
#         travel_user_id = event['travel_user_id']
#         friend_travel_user_id = event['friend_travel_user_id']
#
#         await self.send_json({
#             'type': 'friend_accept',
#             'travel_user_id': travel_user_id,
#             'friend_travel_user_id': friend_travel_user_id,
#             'status': 'acceptance'
#         })
#
#     async def friend_refuse_message(self, event):
#         travel_user_id = event['travel_user_id']
#         friend_travel_user_id = event['friend_travel_user_id']
#
#         await self.send_json({
#             'type': 'friend_refuse',
#             'travel_user_id': travel_user_id,
#             'friend_travel_user_id': friend_travel_user_id,
#             'status': 'refusal'
#         })
#
#     async def friend_block_message(self, event):
#         travel_user_id = event['travel_user_id']
#         friend_travel_user_id = event['friend_travel_user_id']
#
#         await self.send_json({
#             'type': 'friend_block',
#             'travel_user_id': travel_user_id,
#             'friend_travel_user_id': friend_travel_user_id,
#             'status': 'block'
#         })
