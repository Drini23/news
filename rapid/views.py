import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from googletrans import Translator

from django.shortcuts import render
from datetime import datetime, timedelta

from football.settings import S_ALL_SPORT_API


def fetch_livekoora_matches():
    base_url = "https://livekoora.info/"
    url = base_url  # Always use the base URL for today's matches
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    

    soup = BeautifulSoup(response.text, 'html.parser')
    translator = Translator()
    matches = []

    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/matches/' in href:
            full_url = urljoin(base_url, href)
            slug = href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
            decoded_name = unquote(slug).replace('-', ' ')

            # Translate team names to English
            try:
                translated = translator.translate(decoded_name, src='ar', dest='en').text.title()
            except Exception:
                translated = decoded_name.title()

            # Extract match time if available
            time_tag = link.find('time')  # Assuming the match time is within <time> tag
            match_time = time_tag.text.strip() if time_tag else "Unknown"

            matches.append({
                'teams': translated,
                'url': full_url,
                'time': match_time
            })

    return matches


def live_streams_view(request):
    matches = fetch_livekoora_matches()
    return render(request, 'rapid/stream.html', {'matches': matches, 'day': 'Today'})


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