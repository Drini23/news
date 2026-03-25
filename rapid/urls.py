from django.urls import path
from . import views

urlpatterns = [
    
    path('all_sport_api/', views.all_sport_api, name="all_sport_api"),
    path('highlights/', views.highlights, name='highlights'),
    
     path("rapid/new_api/", views.new_api, name="new_api"),
     path("stream/<str:match_id>/", views.get_stream, name="get_stream"),  # use str for match_id
]
