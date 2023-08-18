from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def index(request):
    username = ""
    password = ""
    user = None

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            refresh = request.POST.get('refresh', None)
            if refresh:
                return redirect(request.path)
            else:
                redirect_url = request.POST.get('next', None)
                if redirect_url:
                    return redirect(resolve_url(redirect_url))
                else:
                    return redirect('projectmanagement:home')
        else:
            if username == "" and password == "":
                return render(request, 'registration/login.html', {'error_message': "Please input login credentials"})
            else:
                return render(request, 'registration/login.html',
                              {'error_message': "The provided credentials are incorrect"})
    else:
        return render(request, 'registration/login.html')


def log_out(request):
    logout(request)
    return render(request, 'registration/login.html')
