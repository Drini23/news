
from django.urls import path
from . import views

urlpatterns = [

    # ALL SPORTS API — New URL
    path(
        'football/live/matches/all-sports/streaming-center/api-access/',
        views.all_sport_api,
        name='all_sport_api'
    ),

    # ALL SPORTS API — Old URL
    path(
        'all_sport_api/',
        views.all_sport_api,
        name='all_sport_api_old'
    ),

    # HIGHLIGHTS — New URL
    path(
        'football/video/highlights/match-summaries/',
        views.highlights,
        name='highlights'
    ),

    # HIGHLIGHTS — Old URL
    path(
        'highlights/',
        views.highlights,
        name='highlights_old'
    ),

    # NEW API — New URL
    path(
        'football/live/matches/all-leagues/today/data-feed/',
        views.new_api,
        name='new_api'
    ),

    # NEW API — Old URL
    path(
        'new_api/',
        views.new_api,
        name='new_api_old'
    ),

    # STREAM — New URL
    path(
        'football/live/streaming/match/<str:match_id>/watch/',
        views.get_stream,
        name='get_stream'
    ),

    # STREAM — Old URL
    path(
        'stream/<str:match_id>/',
        views.get_stream,
        name='get_stream_old'
    ),
]
