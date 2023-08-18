import os
import time
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.core.files.uploadedfile import UploadedFile
from ..forms import DocumentForm
from ..models import *


@login_required(login_url='projectmanagement:login')
def all_plans(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = DocumentForm(request.POST, request.FILES)

    plans = Plan.objects.order_by('-date').filter(project_id=project.id)

    context = {'plans': plans, 'project': project, 'form': form}

    return render(request, 'plans/all_plans.html', context)


@login_required(login_url='projectmanagement:login')
def plan_view(plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    pdf_bytes = plan.pdf.read()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{plan.pdf.name}"'

    return response



@login_required(login_url='projectmanagement:login')
def upload_plan(request, project_id):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file: UploadedFile = request.FILES['pdf']
            if uploaded_file.content_type != 'application/pdf':
                return render(request, 'plans/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "Only PDF's allowed."})

            plan = form.save(commit=False)
            name = request.POST.get('name')
            if not name:
                return render(request, 'plans/all_plans.html',
                              {'project': get_object_or_404(Project, pk=project_id), 'form': form,
                               'error_message': "Please enter a name for the plan."})

            plan.name = name
            plan.edited_by = request.user.username
            plan.date = datetime.now()
            plan.project_id = get_object_or_404(Project, pk=project_id)
            plan.save()
            form.save_m2m()

            return redirect('projectmanagement:all_plans', project_id=project_id)
        else:
            return render(request, 'plans/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "File upload failed."})
    else:
        form = DocumentForm()

    return render(request, 'plans/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form})


@login_required(login_url='projectmanagement:login')
def delete_plan(request, project_id):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        print("Attempting to delete plan "+ plan_id)
        # Delete the PDF file from storage
        document = get_object_or_404(Plan, pk=plan_id)
        file_path = document.pdf.path
        if os.path.exists(file_path):
            time.sleep(3)
            os.remove(file_path)
            document.delete()
            print("Plan deleted")

        return redirect('projectmanagement:all_plans', project_id=project_id)  # Redirect to a success page

    return render(request, 'plans/all_plans.html', {'error_message': "Document could not be deleted."})
