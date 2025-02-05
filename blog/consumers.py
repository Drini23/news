import json
import asyncio
import requests
from datetime import datetime
import pytz
from channels.generic.websocket import AsyncWebsocketConsumer
from football.api import football_api

API_URL = 'http://api.football-data.org/v4/matches'  # Replace with your API
HEADERS = {"X-Auth-Token": football_api}  # Replace with your API key

class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.match_task = asyncio.create_task(self.send_match_updates())

    async def disconnect(self, close_code):
        if self.match_task:
            self.match_task.cancel()

    async def send_match_updates(self):
        """Fetch live match data and send updates to the frontend every 30 seconds."""
        while True:
            matches = await self.get_live_matches()
            print("Sending matches:", matches)  # Add logging here
            await self.send(json.dumps({"matches": matches}))
            await asyncio.sleep(30)  # Update every 30 seconds

    async def get_live_matches(self):
        response = requests.get(API_URL, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            matches = []
            for match in data.get("matches", []):
                home_team = match.get("homeTeam", {}).get("name", "N/A")
                away_team = match.get("awayTeam", {}).get("name", "N/A")
                match_time = self.calculate_match_time(match.get("utcDate", ""), match.get("status", ""))

                # Extract scores (handle missing values)
                home_score = match.get("score", {}).get("fullTime", {}).get("home", 0)
                away_score = match.get("score", {}).get("fullTime", {}).get("away", 0)

                matches.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "match_time": match_time,
                    "home_score": home_score if home_score is not None else 0,
                    "away_score": away_score if away_score is not None else 0,
                })

            return matches
        return []

    def calculate_match_time(self, start_time, status):
        """Ensure match time is never negative."""
        now = datetime.now(pytz.UTC)
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

        if status == "TIMED":
            return "Not Started"

        if status == "HALF_TIME":
            return "45:00 (HT)"

        if status == "FINISHED":
            return "FINISHED"

        elapsed = now - start_dt
        minutes = elapsed.total_seconds() // 60

        if minutes < 0:
            return "Not Started"  # Prevent negative times

        return f"{int(minutes)}:00" if minutes < 90 else "90:00+"
