from django.shortcuts import render
import requests
from football.settings import NEWS_API, TRANSFER_NEWS_API


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
    api_key = NEWS_API
    query = request.GET.get('query', 'football')  # Default to 'football' if no query is provided
    football_news = get_news(api_key, query)
    context = {
        'football_news': football_news
    }
    return render(request, 'news/football_news.html', context)


def transfer_news(request):
    url = "https://football_api12.p.rapidapi.com/players/transfers"

    headers = {
        "x-rapidapi-key": TRANSFER_NEWS_API,
        "x-rapidapi-host": "football_api12.p.rapidapi.com"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False,   # dev only
            timeout=10
        )

        if response.status_code != 200:
            transfer_news = []
        else:
            transfer_news = response.json()  # ✅ FIX HERE

    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        transfer_news = []
    print(transfer_news)
    return render(request, "news/transfer_news.html", {
        "transfer_news": transfer_news
    })