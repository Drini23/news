# urls.py
from django.urls import path
from .views import football_news_view

urlpatterns = [
    path('football-news/', football_news_view, name='football_news'),
]
