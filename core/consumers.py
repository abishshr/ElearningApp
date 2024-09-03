import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async


class EchoConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat functionality.
    Manages WebSocket connections, message reception, and broadcasting to room groups.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.room_name = None

    async def connect(self):
        """
        Handles WebSocket connection initiation.
        Joins the room group based on the room name extracted from the URL.
        """
        # Extract room name from the URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        print(f"[DEBUG] Attempting to connect to room: {self.room_name}")

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        print(f"[DEBUG] Connected to room group: {self.room_group_name}")

        # Accept the WebSocket connection
        await self.accept()
        print(f"[DEBUG] WebSocket connection accepted for room: {self.room_name}")

        # Import models locally to avoid circular import issues
        from .models import ChatMessage

        # Fetch the last 20 messages from the database for this room
        messages = await sync_to_async(list)(
            ChatMessage.objects.filter(room__name=self.room_name).order_by('-timestamp')[:20]
        )

        # Send the messages to the WebSocket
        for message in reversed(messages):
            await self.send(text_data=json.dumps({
                'message': message.message,
                'username': await sync_to_async(lambda: message.user.username)(),
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }))

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the channel from the room group.
        """
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(f"[DEBUG] Disconnected from room group: {self.room_group_name} with close code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receives a message from the WebSocket.
        Saves the message to the database and broadcasts it to the room group.
        """
        print(f"[DEBUG] Received message: {text_data} in room: {self.room_name}")

        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            # Safely check for the user's authentication status
            user = self.scope.get('user')
            username = user.username if user and user.is_authenticated else "Anonymous"
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"[DEBUG] Sending message to room group: {self.room_group_name}")

            # Import models locally to avoid circular import issues
            from .models import ChatMessage, ChatRoom

            # Save message to the database using sync_to_async
            if user and user.is_authenticated:
                chat_room = await sync_to_async(ChatRoom.objects.get)(name=self.room_name)
                await sync_to_async(ChatMessage.objects.create)(
                    user=user,
                    room=chat_room,
                    message=message,
                    timestamp=timezone.now()
                )

            # Send the message to the room group with username and timestamp
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'timestamp': timestamp
                }
            )

    async def chat_message(self, event):
        """
        Handles the broadcast of messages to the WebSocket clients.
        Sends messages to all clients connected to the room.
        """
        message = event['message']
        username = event['username']
        timestamp = event['timestamp']

        print(f"[DEBUG] Broadcasting message: {message} from {username} at {timestamp} to room: {self.room_name}")

        # Send the message to the WebSocket with username and timestamp
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'timestamp': timestamp
        }))
