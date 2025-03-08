import requests
from datetime import date, datetime
import pytz
from django.shortcuts import render
from football.api import football_api

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



def today_matches(request):
    api_url = 'http://api.football-data.org/v4/matches'
    headers = {'X-Auth-Token': football_api}  

    response = requests.get(api_url, headers=headers)
    if response.status_code == 403:
     print("Failed to fetch matches:", response.json())  # Log the response

    if response.status_code == 200:
        match_data = response.json()
        print(match_data)
        matches = match_data.get('matches', [])

        for match in matches:
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
            if match['status'] == 'IN_PLAY':
                match['status_label'] = 'Live'
            elif match['status'] == 'FINISHED':
                match['status_label'] = 'Finished'
            else:
                match['status_label'] = '- : -'
            
            # Fetch streaming URL from SportRadar using your API key
            match['stream_url'] = fetch_streaming_url(match['id'], 'BJtNpYdP2LPbbaSdW4sKWlD3qaxdyIAeqCDZNDgs')

        context = {'matches': matches}
        return render(request, 'blog/today_matches.html', context)
    else:
        error_message = f"Failed to fetch matches from the API. Status code: {response.status_code}"
        return render(request, 'blog/error.html', {'error': error_message})




def fetch_team_details(team_id, headers):
    api_url = f'http://api.football-data.org/v4/teams/{team_id}'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch team details for team ID {team_id}. Status code: {response.status_code}")
        return None