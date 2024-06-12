import json
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from ..models import Subcontractor, Exhibit, ExhibitLineItem


@login_required(login_url='projectmanagement:login')
def todo(request):
    context = {

    }

    return render(request, 'misc/todo.html', context)

@login_required(login_url='projectmanagement:login')
def get_master_format(request):
    with open(os.path.join(Path(__file__).resolve().parent.parent, "static/projectmanagement/data/master_format.json"), 'r') as file:
        data = json.load(file)
    return JsonResponse(data)

@login_required(login_url='projectmanagement:login')
def get_exhibits(request, sub_name):
    subcontractor = Subcontractor.objects.filter(name=sub_name).first()
    exhibits = Exhibit.objects.filter(sub_id=subcontractor)

    # Convert QuerySet to list of dictionaries
    exhibits_list = [exhibit_to_dict(exhibit) for exhibit in exhibits]

    return JsonResponse(exhibits_list, safe=False)

@login_required(login_url='projectmanagement:login')
def get_exhibit_line_items(request, exhibit_id):
    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    line_items = ExhibitLineItem.objects.filter(exhibit_id=exhibit)

    # Convert QuerySet to list of dictionaries
    line_items_list = [model_to_dict(line_item) for line_item in line_items]

    return JsonResponse(line_items_list, safe=False)

def exhibit_to_dict(exhibit):
    return {
        'id': exhibit.id,
        'name': exhibit.name,
        'date': exhibit.date.isoformat(),  # Convert datetime to string
        'total': exhibit.total,
        'sub_id': exhibit.sub_id.id,
        'project_id': exhibit.project_id.id,
        'pdf': exhibit.pdf.url if exhibit.pdf else None,  # Convert FileField to URL
    }

@login_required(login_url='projectmanagement:login')
def get_sub_data(request, sub_name):
    subcontractor = Subcontractor.objects.filter(name=sub_name).first()
    data = model_to_dict(subcontractor)

    return JsonResponse(data)
