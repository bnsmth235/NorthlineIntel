import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.contrib.auth import authenticate, logout, login
import base64
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import datetime
from django.core.files.uploadedfile import UploadedFile

from .forms import DocumentForm
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
            if (username == "" and password == ""):
                return render(request, 'reports/login.html', {'error_message': "Please input login credentials"})
            else:
                return render(request, 'reports/login.html',
                              {'error_message': "The provided credentials are incorrect"})
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

        cur_proj = Project(name=name, last_edit_date=last_edit_date, edited_by=edited_by, status=status,
                           address=address + ", " + city + ", " + state + ", " + zip)
        cur_proj.save()
        print("Project " + cur_proj.name + " has been saved")

        return redirect('reports:home')

    return render(request, 'reports/new_proj.html', {"state_choices": STATE_CHOICES})


@login_required(login_url='reports:login')
def create_draw(request, project_id):
    cur_proj = get_object_or_404(Project, pk=project_id)

    cur_proj.last_edit_date = datetime.now()
    cur_proj.edited_by = request.user.username

    cur_draw = Draw(date=datetime.now(), project_id=cur_proj, edited_by=request.user.username)

    cur_draw.save()
    cur_proj.save()

    return all_draws(request, project_id)


@login_required(login_url='reports:login')
def all_draws(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    draws = Draw.objects.order_by('-date').filter(project_id=project.id)

    context = {'draws': draws, 'cur_proj': project}

    return render(request, 'reports/all_draws.html', context)


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
        cur_proj.address = address + ", " + city + ", " + state + ", " + zip
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
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            cur_proj = get_object_or_404(Project, pk=project_id)
            cur_proj.delete()
            print("Project deleted")
        else:
            print("Username incorrect")

    return redirect('reports:home')


@login_required(login_url='reports:login')
def delete_draw(request, project_id):
    if request.method == 'POST':
        draw_id = request.POST.get('draw_id')
        username = request.POST.get('username')
        print("Attempting to delete draw " + draw_id)

        if username == request.user.username:
            cur_draw = get_object_or_404(Draw, pk=draw_id)
            cur_draw.delete()
            print("Draw deleted")
        else:
            print("Username incorrect")

    return redirect('reports:all_draws', project_id=project_id)


@login_required(login_url='reports:login')
def project_view(request, project_id):
    cur_proj = get_object_or_404(Project, pk=project_id)
    return render(request, 'reports/project_view.html', {'cur_proj': cur_proj})


@login_required(login_url='reports:login')
def all_plans(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = DocumentForm(request.POST, request.FILES)

    plans = Plan.objects.order_by('-date').filter(project_id=project.id)

    context = {'plans': plans, 'cur_proj': project, 'form': form}

    return render(request, 'reports/all_plans.html', context)





@login_required(login_url='reports:login')
def upload_plan(request, project_id):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file: UploadedFile = request.FILES['pdf']
            if uploaded_file.content_type != 'application/pdf':
                return render(request, 'reports/all_plans.html', {'cur_proj': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "Only PDF's allowed."})

            plan = form.save(commit=False)
            name = request.POST.get('name')
            if not name:
                return render(request, 'reports/all_plans.html',
                              {'cur_proj': get_object_or_404(Project, pk=project_id), 'form': form,
                               'error_message': "Please enter a name for the plan."})

            plan.name = name;
            plan.edited_by = request.user.username
            plan.date = datetime.now()
            plan.project_id = get_object_or_404(Project, pk=project_id)
            plan.save()
            form.save_m2m()
            # Process the uploaded PDF file or perform any other necessary operations
            return redirect('reports:all_plans', project_id=project_id)  # Redirect to a success page
        else:
            return render(request, 'reports/all_plans.html', {'cur_proj': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "File upload failed."})
    else:
        form = DocumentForm()

    return render(request, 'reports/all_plans.html', {'cur_proj': get_object_or_404(Project, pk=project_id), 'form': form})


@login_required(login_url='reports:login')
def delete_plan(request, project_id):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        print("Attempting to delete plan "+ plan_id)
        # Delete the PDF file from storage
        document = get_object_or_404(Plan, pk=plan_id)
        file_path = document.pdf.path
        if os.path.exists(file_path):
            os.remove(file_path)
            document.delete()
            print("Plan deleted")

        return redirect('reports:all_plans', project_id=project_id)  # Redirect to a success page

    return render(request, 'reports/all_plans.html', {'error_message': "Document could not be deleted."})

@login_required(login_url='reports:login')
def plan_view(request, plan_id, project_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    pdf_bytes = plan.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/plan_view.html', {'pdf_data': pdf_data, 'plan': plan})
