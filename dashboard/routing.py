from django.urls import re_path
from . import consumers  # Replace 'yourapp' with your Django app name

websocket_urlpatterns = [ 
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]