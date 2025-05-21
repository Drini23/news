import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from googletrans import Translator

from django.shortcuts import render
from datetime import datetime, timedelta

from football.settings import ALL_SPORT_API


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


from django.shortcuts import render
import requests

def all_sport_api(request):
    url = "https://all-sport-live-stream.p.rapidapi.com/api/v2/br/all-live-stream"

    querystring = {"sportId": "1"}

    headers = {
        "x-rapidapi-key": ALL_SPORT_API,
        "x-rapidapi-host": "all-sport-live-stream.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    matches = []

    if response.status_code == 200:
        data = response.json()
        print(data)

        # Data is a list of sport blocks
        if isinstance(data, list):
            for sport in data:
                match_list = sport.get("data")
                if isinstance(match_list, list):
                    for match in match_list:
                        matches.append({
                            'team_one': match.get('team_one_name', 'Unknown'),
                            'team_two': match.get('team_two_name', 'Unknown'),
                            'score': match.get('score', 'vs'),
                            'start_time': match.get('start_time', 'Unknown Time'),
                            'iframe_source': match.get('iframe_source') if match.get('iframe_source') != "MATCH_WILL_BEGIN_SOON" else None,
                            'm3u8_source': match.get('m3u8_source') if match.get('m3u8_source') != "MATCH_WILL_BEGIN_SOON" else None
                        })
        else:
            print("Unexpected data format: not a list")
    else:
        print(f"Failed to fetch data: {response.status_code}")

    context = {'matches': matches}
    return render(request, 'rapid/all_sport_api.html', context)