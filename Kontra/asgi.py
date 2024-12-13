# Kontra/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from dashboard.middleware import JWTAuthMiddlewareStack  # Use your custom middleware stack
from dashboard.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Kontra.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP requests handled by Django's ASGI application
    "websocket": JWTAuthMiddlewareStack(  # Use your JWT AuthMiddlewareStack for WebSockets
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
