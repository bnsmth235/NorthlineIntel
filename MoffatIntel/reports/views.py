from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout, login
from .models import *


def index(request):
    username = ""
    password = ""
    user = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        #user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, 'reports/home.html', {'user': user})
    else:
        if(username == "" and password == ""):
            return(render(request, 'reports/home.html'))
        else:
            return render(request, 'reports/login.html', {'error_message': "The provided credentials are incorrect"})


def log_out(request):
    logout(request)
    return render(request, 'reports/login.html')


def home(request):
    if not request.user.is_authenticated:
           return redirect('%s?next=%s' % ('login/', request.path))
    recent_reports = Report.objects.order_by('-request_date', '-status')[:10]
    context = {'recent_reports': recent_reports}
    return render(request, 'reports/home.html', context)

