from django.shortcuts import render
import requests
from football.api import news_api


def get_news(api_key, query='football'):
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'apiKey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        news = response.json()
        return news['articles']
    else:
        print(f"Failed to fetch news: {response.status_code}")
        return []


def football_news_view(request):
    api_key = news_api
    query = request.GET.get('query', 'football')  # Default to 'football' if no query is provided
    football_news = get_news(api_key, query)
    context = {
        'football_news': football_news
    }
    return render(request, 'news/football_news.html', context)
