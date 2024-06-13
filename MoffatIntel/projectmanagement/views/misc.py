import json
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from ..models import Subcontractor, Exhibit, ExhibitLineItem, Draw, DrawLineItem, Check, LienRelease
from .draws import create_lr


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

@login_required(login_url='projectmanagement:login')
def get_draw_data(request, draw_id):
    draw = get_object_or_404(Draw, pk=draw_id)
    draw_items = DrawLineItem.objects.filter(draw_id=draw.id)

    subs = []
    checks = []

    for draw_item in draw_items:
        sub = get_object_or_404(Subcontractor, pk=draw_item.sub_id.id)
        if sub not in subs:
            subs.append(sub)
        check_set = Check.objects.filter(draw_item_id=draw.id)
        for check in check_set:
            if check not in checks:
                checks.append(check)

    data = {
        'draw': model_to_dict(draw),
        'draw_items': [model_to_dict(draw_item) for draw_item in draw_items],
        'subs': [model_to_dict(sub) for sub in subs],
        'checks': [model_to_dict(check) for check in checks],
    }

    return JsonResponse(data, safe=False)

@login_required(login_url='projectmanagement:login')
def get_lr_for_draw_item(request, draw_item_id, type):
    lr = LienRelease.objects.filter(draw_item_id=draw_item_id).first()
    if not lr:
        print("Creating new lien release")
        create_lr(request, draw_item_id, type)
        lr = get_object_or_404(LienRelease, draw_item_id=draw_item_id)

    lr = lr_to_dict(lr)

    data = {
        'lr': lr
    }

    return JsonResponse(data, safe=False)

def lr_to_dict(lr):
    print(lr)
    return {
        'id': lr.id,
        'draw_item_id': lr.draw_item_id.id,
        'type': lr.type,
        'date': lr.date.isoformat(),
        'pdf': lr.pdf.url if lr.pdf else None,
    }


@login_required(login_url='projectmanagement:login')
def get_check_for_draw_item(request, draw_item_id):
    check = Check.objects.filter(draw_item_id=draw_item_id).first()
    if not check:
        return JsonResponse(None, safe=False)

    check = check_to_dict(check)

    data = {
        'check': check
    }

    return JsonResponse(data, safe=False)

def check_to_dict(check):
    return {
        'id': check.id,
        'check_date': check.check_date.isoformat(),
        'check_num': check.check_num,
        'check_total': check.check_total,
        'date': check.date.isoformat(),
        'pdf': check.check_pdf.url if check.pdf else None,
    }
