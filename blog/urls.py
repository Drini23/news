from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('today/', views.today_matches, name='today_matches'),
    
   # path('worldcup/', views.rapid_sport, name='rapid_sport'),
   # path("get_todays_matches/", views.get_todays_matches_json, name="get_todays_matches"),
   
   path('highlights/', views.highlights, name="highlights"),
   path("fetch-new-video/", views.fetch_new_video, name="fetch_new_video"),  # AJAX URL
   path("api/", views.api, name="api"),
]