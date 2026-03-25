import logging
import requests
import pytz


from urllib.parse import quote
from datetime import date, datetime
from football.settings import  NEWS_API, RAPID_API, FOOTBALL_API


from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache


from django.http import JsonResponse
from django.utils.timezone import now


def home(request):
    url = "https://football-live-streaming-api.p.rapidapi.com/matches"
    headers = {
        "x-rapidapi-key": "ff182b108amshf8e8d9cb53258dbp193014jsn90d493c12420",
        "x-rapidapi-host": "football-live-streaming-api.p.rapidapi.com"
    }

    top_leagues = [
        "Premier League",
        "La Liga",
        "Serie A",
        "Bundesliga",
        "Ligue 1",
        "UEFA Champions League",
        "UEFA Europa League",
        "FIFA World Cup"
    ]

    matches = []
    page = 1
    max_matches = 20

    while True:
        querystring = {"page": str(page), "status": "all"}
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print("❌ ERROR:", response.status_code)
            break

        data = response.json()
        current_page_matches = data.get("matches", [])

        if not current_page_matches:
            break

        for match in current_page_matches:
            league_name = match.get("league_name", "")
            status = match.get("status")  # live, upcoming, finished
            match_time_raw = match.get("match_time")  # string or int

            # Convert to local time safely
            match_time = "TBD"
            local_tz = pytz.timezone("Europe/Warsaw")  # change to your timezone
            try:
                if isinstance(match_time_raw, str):
                    utc_dt = datetime.strptime(match_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    match_time = local_dt.strftime("%H:%M")
                elif isinstance(match_time_raw, int):
                    # treat as Unix timestamp
                    utc_dt = datetime.utcfromtimestamp(match_time_raw)
                    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    match_time = local_dt.strftime("%H:%M")
            except Exception as e:
                print("❌ Time parse error:", match_time_raw, e)

            matches.append({
                "home": match.get("home_team_name"),
                "away": match.get("away_team_name"),
                "home_logo": match.get("home_team_logo"),
                "away_logo": match.get("away_team_logo"),
                "time": match_time,
                "league": league_name,
                "status": status
            })

            if len(matches) >= max_matches:
                break

        if len(matches) >= max_matches:
            break

        page += 1

    # Sort: live first, then top leagues
    matches.sort(key=lambda x: (
        0 if x['status'] == "live" else 1,
        0 if x['league'] in top_leagues else 1
    ))

    return render(request, "blog/home.html", {"matches": matches})
    
    
    
   



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
    




def match_details_1(request):
    url = "https://football-live-streaming-api.p.rapidapi.com/matches"
    headers = {
        "x-rapidapi-key": RAPID_API,
        "x-rapidapi-host": "football-live-streaming-api.p.rapidapi.com"
    }

    top_leagues = [
        "Premier League",
        "La Liga",
        "Serie A",
        "Bundesliga",
        "Ligue 1",
        "UEFA Champions League",
        "UEFA Europa League",
        "FIFA World Cup"
    ]

    matches = []
    page = 1
    max_matches = 20

    while True:
        querystring = {"page": str(page), "status": "all"}
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print("❌ ERROR:", response.status_code)
            break

        data = response.json()
        current_page_matches = data.get("matches", [])

        if not current_page_matches:
            break

        for match in current_page_matches:
            league_name = match.get("league_name", "")
            status = match.get("status")  # live, upcoming, finished
            match_time_raw = match.get("match_time")  # string or int

            # Convert to local time safely
            match_time = "TBD"
            local_tz = pytz.timezone("Europe/Warsaw")  # change to your timezone
            try:
                if isinstance(match_time_raw, str):
                    utc_dt = datetime.strptime(match_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    match_time = local_dt.strftime("%H:%M")
                elif isinstance(match_time_raw, int):
                    # treat as Unix timestamp
                    utc_dt = datetime.utcfromtimestamp(match_time_raw)
                    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    match_time = local_dt.strftime("%H:%M")
            except Exception as e:
                print("❌ Time parse error:", match_time_raw, e)

            matches.append({
                "home": match.get("home_team_name"),
                "away": match.get("away_team_name"),
                "home_logo": match.get("home_team_logo"),
                "away_logo": match.get("away_team_logo"),
                "time": match_time,
                "league": league_name,
                "status": status
            })

            if len(matches) >= max_matches:
                break

        if len(matches) >= max_matches:
            break

        page += 1

    # Sort: live first, then top leagues
    matches.sort(key=lambda x: (
        0 if x['status'] == "live" else 1,
        0 if x['league'] in top_leagues else 1
    ))

    return render(request, "football/match_details_1.html", {"matches": matches})





