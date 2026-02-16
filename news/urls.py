# urls.py
from django.urls import path
from . import views
from .views import football_news_view, transfer_news

urlpatterns = [
    path('football-news/', football_news_view, name='football_news'),
    path('transfer_news/', views.transfer_news, name="transfer_news")
]
