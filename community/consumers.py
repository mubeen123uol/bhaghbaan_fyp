import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope.get('user', AnonymousUser())

        # Check authentication & room permissions
        can_join = await self.check_permissions(self.user, self.room_id)
        if not can_join:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            content = data.get('message', '').strip()
            if not content:
                return

            # Save to database
            msg_data = await self.save_message(self.user, self.room_id, content)

            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': msg_data['id'],
                    'content': msg_data['content'],
                    'sender_id': msg_data['sender_id'],
                    'sender_name': msg_data['sender_name'],
                    'created_at': msg_data['created_at'],
                }
            )
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def check_permissions(self, user, room_id):
        if not user or not user.is_authenticated:
            return False
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.can_access(user)
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, room_id, content):
        room = ChatRoom.objects.get(id=room_id)
        msg = Message.objects.create(room=room, sender=user, content=content)
        return {
            'id': msg.id,
            'content': msg.content,
            'sender_id': user.id,
            'sender_name': user.first_name or user.username,
            'created_at': msg.created_at.strftime('%H:%M'),
        }
