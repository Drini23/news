from django.urls import path
from . import views

urlpatterns = [
    
    path('all_sport_api/', views.all_sport_api, name="all_sport_api"),
    path('highlights/', views.highlights, name='highlights'),
]