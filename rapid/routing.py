from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/matches/', consumers.MatchConsumer.as_asgi()),  # WebSocket URL
]
