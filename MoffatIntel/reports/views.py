from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import datetime

from .models import *

STATE_CHOICES = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]

STATUS_OPTIONS = [("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")]

@ensure_csrf_cookie
def index(request):
    username = ""
    password = ""
    user = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

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
                    return redirect('reports:home')
        else:
            if(username == "" and password == ""):
                return render(request, 'reports/login.html', {'error_message': "Please input login credentials"})
            else:
                return render(request, 'reports/login.html', {'error_message': "The provided credentials are incorrect"})
    else:
        return render(request, 'reports/login.html')


def log_out(request):
    logout(request)
    return render(request, 'reports/login.html')

@login_required(login_url='reports:login')
def home(request):
    recent_projects = Project.objects.order_by('-last_edit_date', '-status')[:5]
    context = {'recent_projects': recent_projects}
    return render(request, 'reports/home.html', context)

@login_required(login_url='reports:login')
def all(request):
    projects = Project.objects.order_by('-last_edit_date', '-status')
    context = {'projects': projects}
    return render(request, 'reports/all_proj.html', context)
@login_required(login_url='reports:login')
def create_proj(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        last_edit_date = datetime.now()
        edited_by = request.user.username
        status = "I"

        if not name or not address or not city or not state or not zip:
            return render(request, 'reports/new_proj.html', {'error_message': "Please fill out all fields",
                                                             'state_choices': STATE_CHOICES})

        if int(zip) < 10000 and zip != "":
            return render(request, 'reports/new_proj.html', {'error_message': "Zip code incorrect",
                                                             'state_choices': STATE_CHOICES})

        cur_proj = Project(name=name, last_edit_date=last_edit_date, edited_by=edited_by, status=status, address=address + ", " + city + ", " + state + "," + zip)
        cur_proj.save()
        print("Project " + cur_proj.name + " has been saved")

        return redirect('reports:home')

    return render(request, 'reports/new_proj.html', {"state_choices": STATE_CHOICES})



@login_required(login_url='reports:login')
def edit_proj(request, project_id):
    cur_proj = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        status = request.POST.get('status')
        last_edit_date = datetime.now()
        edited_by = request.user.username


        if not name or not address or not city or not state or not zip:
            return render(request, 'reports/edit_project.html', {'error_message': "Please fill out all fields",
                                                                'state_choices': STATE_CHOICES,
                                                                'status_options': STATUS_OPTIONS})

        if int(zip) < 10000 and zip != "":
            return render(request, 'reports/edit_project.html', {'error_message': "Zip code incorrect",
                                                                'state_choices': STATE_CHOICES,
                                                                'status_options': STATUS_OPTIONS})

        cur_proj.name = name
        cur_proj.address = address+", "+city+", "+state+", "+zip
        cur_proj.status = status
        cur_proj.last_edit_date = last_edit_date
        cur_proj.edited_by = edited_by
        cur_proj.save()

        return redirect('reports:home')

    cur_proj.address = [x.strip() for x in cur_proj.address.split(',')]
    return render(request, 'reports/edit_project.html', {'cur_proj': cur_proj,
                                                            'state_choices': STATE_CHOICES,
                                                            'status_options': STATUS_OPTIONS})

@login_required(login_url='reports:login')
def delete_proj(request, project_id):
    username = request.POST.get('username')

    if(username == request.user.username):
        cur_proj = get_object_or_404(Project, pk=project_id)
        cur_proj.delete()
        return redirect('reports:home')

    print("Username incorrect")
    return redirect('reports:home')

@login_required(login_url='reports:login')
def project_view(request, project_id):
    cur_proj = get_object_or_404(Project, pk=project_id)
    return render(request, 'reports/project_view.html', {'cur_proj': cur_proj})


