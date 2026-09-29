import logging
import requests
import pytz


from urllib.parse import quote
from datetime import date, datetime
from football.settings import  NEWS_API, RAPID_API, FOOTBALL_API


from django_ratelimit.decorators import ratelimit
from django.core.cache import cache


from django.http import JsonResponse
from django.utils.timezone import now
import requests
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone as django_tz
from django.utils.dateparse import parse_datetime


def home(request):
    

    return render(request, "blog/home.html")
    
    
    
def today_matches(request):
    return render(request, 'blog/today_matches.html')



def fetch_team_details(team_id, headers):
    api_url = f'http://api.football-data.org/v4/teams/{team_id}'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch team details for team ID {team_id}. Status code: {response.status_code}")
        return None
    




BIGBALLS_API_KEY = getattr(settings, "BIGBALLS_API_KEY", "bbs_live_00000jMuCxA4SF6fwMYpBOfyPwmQOQsoUtwfhKJFkfUyK9lO")
BIGBALLS_URL = "https://api.bigballsdata.com/v1/matches"


def match_details_1(request):
    headers = {
        "x-api-key": BIGBALLS_API_KEY,
        "Accept": "application/json"
    }

    # Standard league identifiers for the API
    leagues_to_check = ["epl", "laliga", "seriea", "bundesliga", "ligue1", "ucl"]
    matches = []
    local_tz = django_tz.get_current_timezone()

    print("\n" + "=" * 60)
    print("⚽ FETCHING TODAY'S MATCHES LOG")
    print("=" * 60)

    for league in leagues_to_check:
        params = {
            "sport": "football",
            "league": league,
            "date": "today"  # Strictly filter for today
        }

        try:
            response = requests.get(BIGBALLS_URL, headers=headers, params=params, timeout=5)

            if response.status_code == 200:
                json_data = response.json()
                raw_matches = json_data.get("data") or json_data.get("matches") or []

                print(f"--> [{league.upper()}] Matches found today: {len(raw_matches)}")

                for match in raw_matches:
                    home_obj = match.get("home") or match.get("home_team") or {}
                    away_obj = match.get("away") or match.get("away_team") or {}

                    home_name = home_obj.get("name") if isinstance(home_obj, dict) else str(home_obj or "Home")
                    away_name = away_obj.get("name") if isinstance(away_obj, dict) else str(away_obj or "Away")

                    scores = match.get("score") or match.get("scores") or {}
                    home_goals = scores.get("home", 0) if isinstance(scores, dict) else 0
                    away_goals = scores.get("away", 0) if isinstance(scores, dict) else 0

                    league_obj = match.get("league") or match.get("tournament") or league.upper()
                    tournament = league_obj.get("name") if isinstance(league_obj, dict) else str(league_obj)

                    status = str(match.get("status", "")).lower()
                    is_live = status in ["live", "in_play", "in-progress"]

                    if is_live:
                        match_time = match.get("clock") or match.get("minute") or "LIVE"
                    else:
                        raw_time = match.get("start_time") or match.get("kickoff_utc") or match.get("date")
                        match_time = "TBD"
                        if raw_time:
                            dt = parse_datetime(str(raw_time))
                            if dt:
                                if django_tz.is_naive(dt):
                                    dt = django_tz.make_aware(dt, pytz.timezone.utc)
                                match_time = dt.astimezone(local_tz).strftime("%H:%M")

                    match_info = {
                        "home_team": home_name,
                        "away_team": away_name,
                        "teams_name": f"{home_name} vs {away_name}",
                        "goals": f"{home_goals} - {away_goals}",
                        "tournament": tournament,
                        "time": match_time,
                        "status": "live" if is_live else status,
                    }
                    matches.append(match_info)

                    # Print strictly today's matches
                    print(f"  📌 [{tournament}] {match_time} | {home_name} {home_goals}-{away_goals} {away_name} ({status})")

        except requests.RequestException as e:
            print(f"❌ Error fetching {league}: {e}")

    print(f"\nTOTAL MATCHES TODAY: {len(matches)}")
    print("=" * 60 + "\n")

    return render(request, "blog/match_details_1.html", {"matches": matches})