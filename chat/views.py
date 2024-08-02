import logging
import os

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ChatRoom, Message, User
from .serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.exceptions import ValidationError
from django.http import Http404

logger = logging.getLogger('django')
other_server_url = os.environ.get("OTHER_SERVER_URL")

def verify_jwt(url, cookie):
    headers = {
        'Cookie': cookie
    }

    url = url + "travel-user/reading"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            return {
                'data': response.json()
            }
        else:
            if response.status_code == 401:
                return {'error': 'Token expired', 'status_code': 401}
            return {'error': f'Unexpected status code: {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def refresh_jwt_token(url, cookie):
    headers = {
        'Cookie': cookie
    }
    url = url + "auth/token/refresh"

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'Unexpected status code: {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_friends(url, cookie):
    url = url + "friend/friend-list"
    headers = {
        'Cookie': cookie
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            friends = response.json()
            for friend in friends:
                if not friend.get('friendTravelUserDto') or not friend['friendTravelUserDto'].get('travelUserId'):
                    return {'error': 'Friend list contains user with null travelUserId'}
            return friends
        else:
            return {'error': f'Unexpected status code: {response.status}'}
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

class UserGetAndCreateView(APIView):
    def post(self, request, format=None):

        access_token = request.data.get('jwtToken')
        refresh_token = request.data.get('jwtRefreshToken')

        if not refresh_token:
            return Response({f'error': 'Tokens are missing'}, status=status.HTTP_400_BAD_REQUEST)

        cookie = f"jwtToken={access_token}; jwtRefreshToken={refresh_token}"
        jwt_response = verify_jwt(other_server_url, cookie)

        if 'error' in jwt_response:
            return Response({'error': jwt_response['error']}, status=status.HTTP_401_UNAUTHORIZED)

        data = jwt_response.get('data')

        if not data:
            return Response({'error': 'Invalid response from JWT server'}, status=status.HTTP_401_UNAUTHORIZED)

        travel_user_id = data.get('travelUserId')

        if not travel_user_id:
            return Response({'error': 'Invalid JWT token'}, status=status.HTTP_401_UNAUTHORIZED)

        user, created = User.objects.get_or_create(travel_user_id=travel_user_id)
        user.jwt_token = access_token
        user.jwt_refresh_token = refresh_token
        user.save()

        return Response({'message': 'Token verified', 'travelUserId': travel_user_id}, status=status.HTTP_200_OK)

class ChatRoomListCreateAPIView(APIView):
    def get(self, request, format=None):
        travel_user_id = request.query_params.get('travel_user_id')

        if travel_user_id:
            chat_rooms = ChatRoom.objects.filter(users__travel_user_id=travel_user_id)
        else:
            return Response({'error': 'travel_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        users_data = request.data.get('users', [])
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            travel_user_id = request.data.get('travel_user_id')

            if not travel_user_id or not users_data:
                return Response({'error': 'travel_user_id와 user_ids는 필수입니다.'}, status=status.HTTP_400_BAD_REQUEST)

            new_tokens = {}
            try:
                user = User.objects.get(travel_user_id=travel_user_id)
                cookie = f"jwtToken={user.jwt_token}; jwtRefreshToken={user.jwt_refresh_token}"
                friends_data = get_friends(other_server_url, cookie)

                if 'error' in friends_data:
                    if friends_data.get('status_code') == 401:
                        refresh_response = refresh_jwt_token(other_server_url, cookie)
                        if 'error' in refresh_response:
                            return Response({'error': refresh_response['error']}, status=status.HTTP_401_UNAUTHORIZED)
                        user.jwt_token = refresh_response['jwtToken']
                        user.jwt_refresh_token = refresh_response['jwtRefreshToken']
                        user.save()

                        new_tokens['jwtToken'] = refresh_response['jwtToken']
                        new_tokens['jwtRefreshToken'] = refresh_response['jwtRefreshToken']
                        cookie = f"jwtToken={user.jwt_token}; jwtRefreshToken={user.jwt_refresh_token}"
                        friends_data = get_friends(cookie)
                    if 'error' in friends_data:
                        return Response({'error': friends_data['error']}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    accepted_friends = {friend['friendTravelUserDto']['travelUserId'] for friend in friends_data if friend['friendStatus'] == 'acceptance'}
                    user_ids = [user_data['travel_user_id'] for user_data in users_data]
                    if not all(user_id in accepted_friends for user_id in user_ids):
                        return Response({'error': '모든 사용자들은 방을 만들기 위해 친구여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

                    user_ids.append(travel_user_id)
                    for user_id in user_ids:
                        User.objects.get_or_create(travel_user_id=user_id)

                    room = ChatRoom.objects.create(room_name="New Chat Room")
                    room_users = User.objects.filter(travel_user_id__in=user_ids)
                    room.users.set(room_users)
                    room.save()

                    logger.info(f"Room created with users: {[user.travel_user_id for user in room.users.all()]}")

                    response_data = ChatRoomSerializer(room).data
                    if new_tokens:
                        response_data.update(new_tokens)

                    return Response(response_data, status=status.HTTP_201_CREATED)

            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error creating room: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ChatRoomRetrieveUpdateAPIView(APIView):
    def get_object(self, pk):
        try:
            return ChatRoom.objects.get(pk=pk)
        except ChatRoom.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        chat_room = self.get_object(pk)
        serializer = ChatRoomSerializer(chat_room)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        chat_room = self.get_object(pk)
        serializer = ChatRoomSerializer(chat_room, data=request.data)
        if serializer.is_valid():
            if 'users' in request.data:
                chat_room.users.clear()
                for user_data in request.data['users']:
                    user, _ = User.objects.get_or_create(travel_user_id=user_data['travel_user_id'])
                    chat_room.users.add(user)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageListAPIView(APIView):
    def get(self, request, room_id, format=None):
        if not room_id:
            raise ValidationError('room_id 파라미터가 필요합니다.')
        messages = Message.objects.filter(room_id=room_id)
        if not messages.exists():
            raise Http404('해당 room_id로 메시지를 찾을 수 없습니다.')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)