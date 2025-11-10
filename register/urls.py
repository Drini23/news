from django.urls import path
from .views import login_view, SignUp, logout_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', SignUp.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
]