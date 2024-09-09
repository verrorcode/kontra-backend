import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import UserProfile
from channels.db import database_sync_to_async
from .rag import Querying  # Import the new Querying class

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = f"user_{self.user.id}"
        self.room_group_name = f"chat_{self.room_name}"

        # Fetch user profile to check total credits
        user_profile = await UserProfile.objects.aget(user=self.user)

        total_credits = user_profile.credits + user_profile.recharge_credits

        if total_credits < 10:  # Require at least 10 credits to start
            await self.send(text_data=json.dumps({
                'message': "Insufficient credits. You need at least 10 credits to start."
            }))
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Fetch user profile to check total credits
        user_profile = await UserProfile.objects.aget(user=self.user)
        total_credits = user_profile.credits + user_profile.recharge_credits

        if total_credits < 10:
            await self.send(text_data=json.dumps({
                'message': "Insufficient credits. You need at least 10 credits to continue."
            }))
            return

        # Use the Querying class to process the query
        query_processor = Querying(self.user.id)
        answer = await database_sync_to_async(query_processor.query)(message)

        # Deduct 10 credits for each query
        await self.deduct_credits(user_profile)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': answer
        }))

    @database_sync_to_async
    def deduct_credits(self, user_profile):
        total_credits = user_profile.credits + user_profile.recharge_credits

        # Deduct credits first from recharge_credits, then from plan credits
        if user_profile.recharge_credits >= 10:
            user_profile.recharge_credits -= 10
        elif total_credits >= 10:
            remaining_credits = 10 - user_profile.recharge_credits
            user_profile.recharge_credits = 0
            user_profile.credits -= remaining_credits

        user_profile.save()
