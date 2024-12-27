
import requests

from datetime import date, datetime
import pytz
from django.shortcuts import render


football_api = 'b4514c7269ac429687a8f80cad6b9dfe'

#"http://api.football-data.org/v4/teams/2061" -H "X-Auth-Token: <YOUR_API_KEY>"


api_url = 'http://api.football-data.org/v4/matches/327117'




headers = {'X-Auth-Token': football_api}

# Make the GET request
response = requests.get(api_url, headers=headers)

# Check and print the response
if response.status_code == 200:
    data = response.json()
    
    print(f"Short Name: {data['shortName']}")
    print(f"Website: {data['website']}")
else:
    print(f"Error {response.status_code}: {response.text}")