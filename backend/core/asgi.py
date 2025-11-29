"""
ASGI config for AI SURVEILLENCE SYSTEM2 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
[https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/](https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/)
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

# FIX APPLIED: Using the correct settings module path.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')

# Import WebSocket routing after setting DJANGO_SETTINGS_MODULE
from backend.surveillance_app.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
