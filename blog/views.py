import logging
import requests
import pytz
from urllib.parse import quote

from datetime import date, datetime

from football.settings import  NEWS_API, RAPID_API, FOOTBALL_API


from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache


import json
from django.http import JsonResponse
from django.utils.timezone import now


def home(request):
    return render(request, 'blog/home.html')



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
    







