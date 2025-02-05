from django.urls import re_path
from .consumers import MatchConsumer

websocket_urlpatterns = [
    re_path(r"ws/matches/$", MatchConsumer.as_asgi()),
]
