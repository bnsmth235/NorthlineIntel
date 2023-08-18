import os
import time
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime

from django.utils.baseconv import base64

from ..models import Project, Estimate, DIVISION_CHOICES


@login_required(login_url='projectmanagement:login')
def all_estimates(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    estimates = Estimate.objects.filter(project_id = project).order_by('csi')

    context = {
        'project': project,
        'estimates': estimates,
        'divisions': DIVISION_CHOICES,
    }

    return render(request, 'estimates/all_estimates.html', context)


@login_required(login_url='projectmanagement:login')
def delete_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = estimate.project_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(estimate.pdf.path):
            time.sleep(3)
            os.remove(estimate.pdf.path)
            estimate.delete()

    return redirect('projectmanagement:all_estimates', project_id=project.id)


@login_required(login_url='projectmanagement:login')
def estimate_pdf_view(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    pdf_bytes = estimate.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'estimates/estimate_pdf_view.html', {'pdf_data': pdf_data, 'estimate': estimate})

