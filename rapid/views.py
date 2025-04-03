import requests
import logging
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timezone
from django.utils.timezone import now
from django.views.decorators.cache import cache_page

logger = logging.getLogger(__name__)

# Top competitions dictionary (matches your template)
TOP_COMPETITIONS = {
    # Domestic Leagues
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    94: "Primeira Liga",
    88: "Eredivisie",
    253: "MLS",

    # European Competitions
    2: "Champions League",
    3: "Europa League",
    848: "Europa Conference League",

    # Domestic Cups
    137: "Coppa Italia",
    143: "Copa del Rey",
    45: "FA Cup",
    529: "DFB Pokal",
    66: "Coupe de France",

    # International
    1: "World Cup",
    15: "FIFA Club World Cup",
    13: "UEFA Nations League"
}


@cache_page(60 * 5)  # Cache for 5 minutes
def get_todays_matches(request):
    """
    Fetch today's matches from top competitions only
    """
    try:
        # API Configuration
        BASE_URL = "https://v3.football.api-sports.io"
        HEADERS = {
            "x-rapidapi-key": "5a66037bbb5dbd160f1d96d29a3b4214",
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        # Get date from request or use today
        date_param = request.GET.get('date')
        if date_param:
            try:
                requested_date = datetime.strptime(date_param, "%Y-%m-%d").date()
                query_date = requested_date.strftime("%Y-%m-%d")
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=400
                )
        else:
            query_date = now().strftime("%Y-%m-%d")

        logger.info(f"Fetching top competitions matches for {query_date}")

        # Fetch matches
        fixtures_params = {
            "date": query_date,
            "timezone": "UTC"
        }

        try:
            response = requests.get(
                f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params=fixtures_params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            if data.get('errors'):
                logger.error(f"API Error: {data['errors']}")
                return JsonResponse(
                    {"error": data['errors']},
                    status=response.status_code
                )

            all_matches = data.get('response', [])

            # Filter matches to only include top competitions
            matches = [match for match in all_matches
                       if match.get('league', {}).get('id') in TOP_COMPETITIONS]

            logger.info(f"Found {len(matches)} matches in top competitions")

        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Failed: {str(e)}")
            return JsonResponse(
                {"error": str(e)},
                status=500
            )

        # Process matches
        processed_matches = []
        live_matches = []
        competitions = {}
        now_time = datetime.now(timezone.utc)

        for match in matches:
            try:
                fixture = match.get('fixture', {})
                league = match.get('league', {})
                teams = match.get('teams', {})
                goals = match.get('goals', {})
                status = fixture.get('status', {})

                # Calculate match time and status
                match_time = fixture.get('date')
                match_datetime = datetime.strptime(match_time, "%Y-%m-%dT%H:%M:%S%z") if match_time else None

                elapsed = None
                if match_datetime and status.get('short') in ["1H", "HT", "2H"]:
                    total_mins = int((now_time - match_datetime).total_seconds() // 60)
                    if status['short'] == "1H":
                        elapsed = min(total_mins, 45)
                    elif status['short'] == "HT":
                        elapsed = "HT"
                    elif status['short'] == "2H":
                        elapsed = max(1, total_mins - 45)

                # Store competition info
                league_id = league.get('id')
                if league_id:
                    competitions[league_id] = {
                        'name': TOP_COMPETITIONS.get(league_id, league.get('name')),
                        'country': league.get('country', 'International'),
                        'logo': league.get('logo'),
                        'flag': league.get('flag'),
                        'is_cup': league_id in [137, 143, 45, 529, 66, 1, 15, 13]  # Cup competitions
                    }

                match_data = {
                    'id': fixture.get('id'),
                    'time': match_time,
                    'status': status.get('long'),
                    'is_live': status.get('short') in ["1H", "HT", "2H"],
                    'elapsed': elapsed,
                    'league_id': league_id,
                    'league_name': TOP_COMPETITIONS.get(league_id, league.get('name')),
                    'country': league.get('country', 'International'),
                    'home_team': teams.get('home', {}).get('name'),
                    'away_team': teams.get('away', {}).get('name'),
                    'home_logo': teams.get('home', {}).get('logo', '/static/images/default_logo.png'),
                    'away_logo': teams.get('away', {}).get('logo', '/static/images/default_logo.png'),
                    'home_score': goals.get('home', '-'),
                    'away_score': goals.get('away', '-'),
                    'venue': fixture.get('venue', {}).get('name'),
                    'referee': fixture.get('referee'),
                    'is_cup': league_id in [137, 143, 45, 529, 66, 1, 15, 13]  # For template styling
                }

                processed_matches.append(match_data)
                if match_data['is_live']:
                    live_matches.append(match_data)

            except Exception as e:
                logger.error(f"Error processing match: {str(e)}")
                continue

        return JsonResponse({
            'success': True,
            'date': query_date,
            'matches': processed_matches,
            'live_matches': live_matches,
            'competitions': competitions,
            'count': len(processed_matches),
            'live_count': len(live_matches)
        })

    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}")
        return JsonResponse({
            'error': 'Server error',
            'details': str(e)
        }, status=500)


def rapid_sport(request):
    """Render the matches page with live updating"""
    context = {
        'page_title': "Top Football Matches",
        'refresh_interval': 120  # Refresh every 2 minutes
    }
    return render(request, 'rapid/rapid_sport.html', context)

