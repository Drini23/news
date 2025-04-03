from django.urls import path
from . import views

urlpatterns = [
    path("rapid_sport/", views.rapid_sport, name="rapid_sport"),
    path("get_todays_matches/", views.get_todays_matches, name="get_todays_matches"),
]