from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout

from MoffatIntel.MoffatIntel import settings
from MoffatIntel.reports.models import *


def index(request, user):
    if(request.method == 'POST'):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
    else:
        return render(request, 'reports/login.html', {'error_message': "The provided credientials are incorrect"})


def login(request, user):
    if check_auth(request):
        return render(request, 'reports/home.html', {'user': user})
    else:
        log_out(request)

def log_out(request):
    logout(request)
    return render(request, 'reports/login.html')


def home(request, user):
    recent_reports = Report.objects.order_by('-request_date', '-status')[:10]
    context = {'recent_reports': recent_reports}
    return render(request, 'reports/home.html', context)

def check_auth(request):
    if not request.user.is_authenticated:
        return False
    else:
        return True