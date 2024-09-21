import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import UserProfile
from channels.db import database_sync_to_async
from .rag import Querying  # Import the new Querying class
from django.db import transaction

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = f"user_{self.user.id}"
        self.room_group_name = f"chat_{self.room_name}"


        await self.accept()
        # Fetch user profile to check total credits
        user_profile = await UserProfile.objects.aget(user=self.user)

        total_credits = user_profile.credits + user_profile.recharged_credits

        if total_credits < 10:  # Require at least 10 credits to start
            await self.send(text_data=json.dumps({
                'message': "Insufficient credits. You need at least 10 credits to start."
            }))
            await self.close()
            return
        self.query_processor = Querying(self.user.id)
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        

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
        total_credits = user_profile.credits + user_profile.recharged_credits

        if total_credits < 10:
            await self.send(text_data=json.dumps({
                'message': "Insufficient credits. You need at least 10 credits to continue."
            }))
            return

        # Use the Querying class to process the query
       
        answer = await database_sync_to_async(self.query_processor.query)(message)

        # Convert answer to a serializable format if needed
        if isinstance(answer, (dict, list)):
            serialized_answer = answer
        else:
            serialized_answer = str(answer)  # or use another appropriate serialization

        # Deduct 10 credits for each query
        await self.deduct_credits(user_profile)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': serialized_answer
        }))


    @database_sync_to_async
    def deduct_credits(self, user_profile):
        try:
            with transaction.atomic():
                user_profile = UserProfile.objects.select_for_update().get(pk=user_profile.pk)
                total_credits = user_profile.credits + user_profile.recharged_credits

                # Deduct credits correctly based on available credits in both fields
                if user_profile.recharged_credits >= 10:
                    user_profile.recharged_credits -= 10
                elif user_profile.recharged_credits > 0:  # Deduct remaining recharged credits first
                    remaining_deduction = 10 - user_profile.recharged_credits
                    user_profile.recharged_credits = 0
                    user_profile.credits -= remaining_deduction
                elif user_profile.credits >= 10:
                    user_profile.credits -= 10
                else:
                    raise ValueError("Insufficient credits")

                user_profile.save()
                print(f"Credits successfully deducted. Credits: {user_profile.credits}, Recharged credits: {user_profile.recharged_credits}")

        except Exception as e:
            print(f"Error deducting credits: {e}")