import logging
import requests
import pytz
from urllib.parse import quote

from datetime import date, datetime
from football.api import football_api

from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache


import json
from django.http import JsonResponse
from django.utils.timezone import now


def home(request):
    return render(request, 'blog/home.html')


def fetch_streaming_url(match_id, api_key):
    # This function should contain logic to get the streaming URL from the appropriate API
    # Here's a placeholder that simulates fetching a stream URL:
    stream_url_api = f'http://api.sportradar.com/v4/matches/{match_id}/streams'  # Example URL
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(stream_url_api, headers=headers)

    if response.status_code == 200:
        stream_data = response.json()
        # Assuming the streaming data structure contains a `url` field:
        return stream_data.get('url', 'No stream available')
    else:
        return 'No stream available'



logger = logging.getLogger(__name__)

@ratelimit(key='ip', rate='10/m', method='GET', block=True)
def today_matches(request):
    api_url = 'http://api.football-data.org/v4/matches'
    headers = {'X-Auth-Token': football_api}
    
    
    # Check if matches are cached
    cached_matches = cache.get("todays_matches")
    if cached_matches:
        return render(request, "blog/today_matches.html", {"matches": cached_matches})
    
    # Fetch matches from the API if not cached
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx, 5xx)
    except requests.exceptions.HTTPError as errh:
        logger.error(f"HTTP error occurred: {errh}")
        return render(request, 'blog/error.html', {'error': 'Failed to fetch matches from API (HTTP error).'})
    except requests.exceptions.RequestException as err:
        logger.error(f"Error occurred: {err}")
        return render(request, 'blog/error.html', {'error': 'An error occurred while fetching the matches.'})

    # Process the match data
    match_data = response.json()
    matches = match_data.get('matches', [])
    for match in matches:
        match = process_match_data(match)
    
    # Cache the matches with an expiration time (e.g., 10 minutes)
    cache.set("todays_matches", matches, timeout=600)
    
    
    
    return render(request, 'blog/today_matches.html', {'matches': matches, })


def process_match_data(match):
    """Helper function to process individual match data."""
    # Parse and format the match time
    utc_date = match['utcDate']
    match_time = datetime.fromisoformat(utc_date.replace('Z', '+00:00'))
    local_time = match_time.astimezone(pytz.timezone('Europe/Warsaw'))  # Adjust to your timezone
    match['formatted_time'] = local_time.strftime('%Y-%m-%d %H:%M')

    # Extract match scores
    score = match.get('score', {})
    full_time = score.get('fullTime', {})
    match['home_team_score'] = full_time.get('home', '-') if full_time.get('home') is not None else '-'
    match['away_team_score'] = full_time.get('away', '-') if full_time.get('away') is not None else '-'
    
    # Status-specific handling
    match['status_label'] = 'Live' if match['status'] == 'IN_PLAY' else 'Finished' if match['status'] == 'FINISHED' else '- : -'
    
    # Fetch streaming URL
    match['stream_url'] = fetch_streaming_url(match['id'], 'BJtNpYdP2LPbbaSdW4sKWlD3qaxdyIAeqCDZNDgs')
    
    return match


def fetch_team_details(team_id, headers):
    api_url = f'http://api.football-data.org/v4/teams/{team_id}'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch team details for team ID {team_id}. Status code: {response.status_code}")
        return None
    

API_KEY = "AIzaSyCOXlN5-3JK95GMjuKo5kpZwqUrmi5DJWI"
SEARCH_QUERY = (
    "Premier League Highlights | La Liga Highlights | Bundesliga Highlights | Serie A Highlights | "
    "Ligue 1 Highlights | Champions League Highlights | Europa League Highlights | FIFA World Cup Highlights | UEFA Euro Highlights"
)
MAX_RESULTS = 15  # Fetch more videos

def get_youtube_videos():
    """Fetch highlights from YouTube API"""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={SEARCH_QUERY}&type=video&key={API_KEY}&maxResults={MAX_RESULTS}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        videos = [
            {"title": item["snippet"]["title"], "videoId": item["id"]["videoId"]}
            for item in data.get("items", [])
        ]
        return videos
    return []

def fetch_new_video(request):
    """Return a new video when a user removes one"""
    existing_videos = request.GET.getlist("existing_videos[]")  # Get list of already displayed videos
    videos = get_youtube_videos()

    # Find a video that is not already displayed
    new_video = next((v for v in videos if v["videoId"] not in existing_videos), None)

    if new_video:
        return JsonResponse(new_video)
    return JsonResponse({"error": "No new videos found"}, status=404)





def highlights(request):
    """Render the highlights page"""
    videos = get_youtube_videos()
    return render(request, "blog/highlights.html", {"data": videos})



def api(request):
    API_KEY = "AIzaSyCOXlN5-3JK95GMjuKo5kpZwqUrmi5DJWI"  # Replace with your actual API key
    SEARCH_QUERY = request.GET.get("q", "Live Football Match")  # More specific search
    MAX_RESULTS = 20  # Number of results to fetch

    # Construct the API URL with better filtering
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&q={SEARCH_QUERY}"
        f"&type=video&eventType=live"
        f"&videoCategoryId=17"  # Sports category
        f"&key={API_KEY}&maxResults={MAX_RESULTS}"
    )

    # Fetch data from the YouTube API
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # Filter out fake matches (optional)
        real_matches = []
        for item in data.get("items", []):
            title = item["snippet"]["title"].lower()
            description = item["snippet"]["description"].lower()

            if any(keyword in title for keyword in ["live", "football", "match", "league"]):
                real_matches.append(item)

        return render(request, "blog/api.html", {"data": {"items": real_matches}, "query": SEARCH_QUERY})

    return render(request, "blog/api.html", {"error": "Failed to fetch data from YouTube API."})