"""
ASGI config for virtual_office project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from channels.auth import AuthMiddlewareStack
from communications.middleware import JWTAuthMiddleware
import communications.routing
import accounts.wallet.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_office.settings')

# Combine both apps' websocket URL patterns into one list
websocket_urlpatterns = (
    communications.routing.websocket_urlpatterns
    + accounts.wallet.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})

print("✅ ASGI application loaded (Channels is active)")
