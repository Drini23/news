from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.http import HttpResponse

from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Create your views here.

def login_view(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        ueser = authenticate(request, username=username, password=password)
        if ueser is not None:
            login(request, ueser)
            return redirect('home')
        else:
            return HttpResponse('Invalid credentials')
    context = {"login_view": "active"}
    
    return render(request, 'register/login.html', context)




    
class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'register/register.html'


def logout_view(request):
    
    logout(request)
    return redirect('home') 
    return render(request, 'register/logout.html')