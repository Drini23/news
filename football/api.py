football_api = 'b4514c7269ac429687a8f80cad6b9dfe'
news_api = 'c432527482b94f29b6075da87fb8e3c0'
rapid_api = "34b0bd35cc285d9fd875c441ab9e6920"

import requests
import json

# Make sure you have a valid API key


# Set the endpoint and headers for the request
uri = 'https://api.football-data.org/v4/matches'
headers = { 'X-Auth-Token': football_api }

# Send the GET request to the API
response = requests.get(uri, headers=headers)

# Check if the response was successful
if response.status_code == 200:
    response_json = response.json()
    
    # Check if 'matches' key exists in the response
    if 'matches' in response_json:
        for match in response_json['matches']:
            print(match)  # Print each match data
    else:
        print("No matches found in the response:", response_json)
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
    print("Error response:", response.text)  # Print error details from the API
