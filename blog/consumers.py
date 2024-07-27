# consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Match

class MatchConsumer(WebsocketConsumer):
    def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group_name = 'match_%s' % self.match_id

        # Join match group
        async_to_sync(self.channel_layer.group_add)(
            self.match_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave match group
        async_to_sync(self.channel_layer.group_discard)(
            self.match_group_name,
            self.channel_name
        )

    # Receive live updates from server and send to WebSocket
    def match_update(self, event):
        match_data = event['data']
        # Send match data to WebSocket
        self.send(text_data=json.dumps({
            'type': 'match_update',
            'data': match_data
        }))
