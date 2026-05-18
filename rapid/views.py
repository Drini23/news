import requests
from django.shortcuts import render
from football.settings import S_ALL_SPORT_API
from functools import lru_cache

@lru_cache(maxsize=128)
def all_sport_api(request):
    # NEW endpoint (working)
    url = "https://all-sport-live-stream.p.rapidapi.com/api/d/match_list"
    querystring = {"sportId": "1"}

    headers = {
        "x-rapidapi-key": S_ALL_SPORT_API,
        "x-rapidapi-host": "all-sport-live-stream.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    matches = []

    if response.status_code == 200:
        data = response.json()

        # NEW response structure
        if "data" in data and "t1" in data["data"]:
            for match in data["data"]["t1"]:

                # only LIVE matches
                if not match.get("iplay", False):
                    continue

                gmid = match.get("gmid")

                matches.append({
                    # keep old keys so template DOES NOT CHANGE
                    "teams_name": match.get("ename", "Unknown"),
                    "team_two": match.get("cname", "Unknown"),
                    "score": match.get("sc", "vs"),
                    "start_time": match.get("stime", "Live"),

                    # iframe stream (constructed)
                    "iframe_source": (
                        f"https://livestream-v3-iframe.akamaized.uk/directStream"
                        f"?gmid={gmid}&key=nokey"
                        if gmid else None
                    ),

                    # this API does NOT provide m3u8
                    "m3u8_source": None,
                })
        else:
            print("Unexpected data format")

    else:
        print(f"Failed to fetch data: {response.status_code}")

    context = {"matches": matches}
    return render(request, "rapid/all_sport_api.html", context)

def highlights(request):
    return render(request, 'rapid/highlights.html')




import requests
from django.shortcuts import render
from django.http import JsonResponse

API_KEY = "ff182b108amshf8e8d9cb53258dbp193014jsn90d493c12420"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "football-live-stream-api.p.rapidapi.com",
}


def new_api(request):

    url = "https://football-live-stream-api.p.rapidapi.com/all-match"

    matches = []

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        print("STATUS:", response.status_code)

        data = response.json()

        print("API RESPONSE:", data)

        if response.status_code == 200:

            for match in data.get("result", []):

                matches.append({
                    "id": match.get("id"),
                    "home_name": match.get("home_name", "Unknown"),
                    "away_name": match.get("away_name", "Unknown"),
                    "score": match.get("score", "0 - 0"),
                    "status": match.get("status", "N/A"),
                })

    except requests.exceptions.RequestException as e:

        print("API ERROR:", e)

    return render(request, "rapid/new_api.html", {
        "matches": matches
    })
    
    
    
import base64

def get_stream(request, match_id):

    url = f"https://football-live-stream-api.p.rapidapi.com/link/{match_id}"

    response = requests.get(url, headers=HEADERS)
    data = response.json()

    raw = data.get("url")

    # extract base64 part
    try:
        encoded = raw.split("url=")[1]
        decoded_url = base64.b64decode(encoded).decode("utf-8")

    except:
        decoded_url = raw

    return render(request, "rapid/player.html", {
        "stream_url": decoded_url
    })