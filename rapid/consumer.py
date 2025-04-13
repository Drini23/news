import json
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'match_updates'  # Group name for broadcasting messages
        # Add this WebSocket connection to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Remove this WebSocket connection from the group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle any messages received from the WebSocket client if needed
        pass

    async def send_match_data(self, event):
        # Send match data to WebSocket client(s)
        await self.send(text_data=json.dumps({
            'matches': event['matches'],
            'live_matches': event['live_matches'],
            'competitions': event['competitions'],
        }))

    async def fetch_and_broadcast_matches(self):
        # Fetch match data from the API
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": "5a66037bbb5dbd160f1d96d29a3b4214",
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timezone": "UTC"
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        matches = []  # Process matches here as you did in your Django view
        live_matches = []
        competitions = {}

        # Process the matches (same as you did in the view)...
        
        # Send the processed data to all WebSocket clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_match_data',
                'matches': matches,
                'live_matches': live_matches,
                'competitions': competitions
            }
        )
