from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('today/', views.today_matches, name='today_matches'),
    
   
   
  
   
]