from django.urls import path
from . import views

urlpatterns = [
    path('streams/', views.live_streams_view, name='stream'),
    
    path('all_sport_api/', views.all_sport_api, name="all_sport_api")
]