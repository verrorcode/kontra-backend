from django.urls import path
from . import consumers

websocket_urlpatterns = [
   
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),  # Example WebSocket route
    # Add more WebSocket paths and corresponding consumers as needed
]

