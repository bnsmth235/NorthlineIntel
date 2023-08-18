from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Project, Draw, Group, Subgroup, Subcontractor, Vendor, Report


@login_required(login_url='projectmanagement:login')
def reports(request):
    reports = Report.objects.order_by('-date')
    return render(request, 'projectmanagement/all_reports.html', {'projectmanagement': reports})
