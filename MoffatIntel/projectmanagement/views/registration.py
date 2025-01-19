from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from axes.handlers.database import AxesDatabaseHandler
from axes.handlers.proxy import AxesProxyHandler
import random
import string
import os
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64

TEMP_PASSWORD_EXPIRATION_HOURS = 24

def generate_temp_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def get_oauth2_tokens():
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": os.getenv('CLIENT_ID'),
                "client_secret": os.getenv('CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["https://www.moffatintel.com/projectmanagement", "http://localhost:61466/"],
            }
        },
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    credentials = flow.run_local_server(port=61466)
    return credentials.token, credentials.refresh_token

def send_email_with_oauth2(to, subject, body):
    access_token, refresh_token = get_oauth2_tokens()
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.SOCIALACCOUNT_PROVIDERS['google']['CLIENT_ID'],
        client_secret=settings.SOCIALACCOUNT_PROVIDERS['google']['CLIENT_SECRET'],
    )
    service = build('gmail', 'v1', credentials=credentials)
    message = {
        'raw': base64.urlsafe_b64encode(
            f'To: {to}\nSubject: {subject}\n\n{body}'.encode('utf-8')
        ).decode('utf-8')
    }
    service.users().messages().send(userId='me', body=message).execute()

def request_login(request):
    if request.method == 'POST':
        first_name = request.POST.get('first-name')
        last_name = request.POST.get('last-name')
        username = request.POST.get('username')
        email = request.POST.get('email')

        if not first_name or not last_name or not username or not email:
            print("Please fill in all fields")
            return render(request, 'registration/request_login.html', {'error_message': "Please fill in all fields"})

        try:
            print("Checking if user exists")
            user = User.objects.get(username=username)
            return render(request, 'registration/request_login.html', {'error_message': "The username already exists"})
        except User.DoesNotExist:
            print("User does not exist, creating user")
            temp_password = generate_temp_password()

            print("Sending email")

            send_email_with_oauth2(
                to="moffatintel.a@gmail.com",
                subject=f'User {username} Requests Login',
                body=f'{first_name} {last_name} has requested a login. Their username is {username} and their temporary '
                     f'password is {temp_password}\n\nEmail: {email} their username and temporary password to approve '
                     f'the account creation.\n\nThanks,\nMoffatIntel Automation',
            )

            user = User.objects.create_user(username=username, email=email, password=temp_password,
                                            first_name=first_name, last_name=last_name)
            user.profile.temp_password_expiration = timezone.now() + timedelta(hours=TEMP_PASSWORD_EXPIRATION_HOURS)
            user.save()

            return render(request, 'registration/request_login.html', {'success_message': "Your request has been submitted. You will receive an email once your account has been approved."})
    else:
        return render(request, 'registration/request_login.html')
@ensure_csrf_cookie
def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            if user.profile.temp_password_expiration and user.profile.temp_password_expiration > timezone.now():
                if user.check_password(password):
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
                    if AxesDatabaseHandler.is_locked(AxesProxyHandler(), request=request):
                        return render(request, 'registration/login.html', {'error_message': "Account locked: too many login attempts"})
                except Exception as e:
                    pass

            return render(request, 'registration/login.html', {'error_message': "The provided credentials are incorrect"})
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

        if password == confpassword:
            # Get the user based on the username
            user = User.objects.get(username=username)

            # Set the new password for the user
            user.set_password(password)

            # Turn off the temporary password functionality
            user.profile.temp_password_expiration = None

            # Save the user to update the password and temporary password expiration
            user.save()

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

