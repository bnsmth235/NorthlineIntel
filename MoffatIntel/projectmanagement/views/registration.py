from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from axes.handlers.database import AxesDatabaseHandler
from axes.handlers.proxy import AxesProxyHandler

DEFAULT_PASSWORD = "temp_password"
@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            if password == DEFAULT_PASSWORD:
                print("redirecting....")
                return redirect('projectmanagement:change_password', username=username)

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
                try:
                    # Check if the account is locked
                    if AxesDatabaseHandler.is_locked(AxesProxyHandler(), request=request):
                        print("USER IS LOCKED")
                        return render(request, 'registration/login.html',
                                      {
                                          'error_message': "Account locked: too many login attempts"})
                except Exception as e:
                    print("****************** EXCEPTION: " + str(e))
                    pass  # Handle other exceptions as needed

            return render(request, 'registration/login.html',
                          {'error_message': "The provided credentials are incorrect"})
    else:
        return render(request, 'registration/login.html')


def lockout(request, credentials):
    return render(request, 'registration/login.html',
                  {
                      'error_message': "Account locked: too many login attempts"})


def change_password(request, username):
    if request.method == "POST":
        password = request.POST.get('password')
        confpassword = request.POST.get('confpassword')

        print(password, confpassword)
        if password == confpassword:
            # Get the user based on the username
            user = User.objects.get(username=username)
            print("user: " , str(user))
            # Set the new password for the user
            user.set_password(password)

            # Save the user to update the password
            user.save()
            print("user saved")

            # Redirect to a success page or login page
            return redirect('projectmanagement:login')  # Change this to your login URL
        else:
            error_message = "Passwords do not match"
            return render(request, 'registration/change_password.html',
                          {'username': username, 'error_message': error_message})

    else:
        return render(request, 'registration/change_password.html', {'username': username})


def log_out(request):
    logout(request)
    return render(request, 'registration/login.html')
