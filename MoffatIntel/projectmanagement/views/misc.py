import json
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.shortcuts import render, get_object_or_404
from ..models import Subcontractor, Exhibit, ExhibitLineItem, Draw, DrawLineItem, Check, LienRelease, \
    DrawSummaryLineItem
from .draws import create_lr
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
def get_exhibits(request, sub_name, project_id):
    subcontractor = Subcontractor.objects.filter(name=sub_name).first()
    exhibits = Exhibit.objects.filter(sub_id=subcontractor).filter(project_id=project_id)

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

    # Initialize a dictionary to store the draw items and their sum for each subcontractor
    sub_draw_items = {}

    for draw_item in draw_items:
        sub = get_object_or_404(Subcontractor, pk=draw_item.sub_id.id)
        if sub not in subs:
            subs.append(sub)
        check_set = Check.objects.filter(draw_item_id=draw.id)
        for check in check_set:
            if check not in checks:
                checks.append(check)

        # Add the draw item to the subcontractor's list and update the sum
        if sub.id not in sub_draw_items:
            sub_draw_items[sub.id] = {"draw_item": model_to_dict(draw_item), "sum": 0}
        sub_draw_items[sub.id]["sum"] += draw_item.draw_amount  # Replace 'draw_amount' with the actual field name

    for sub in subs:
        draw_summary_item = DrawSummaryLineItem.objects.filter(draw_id=draw, sub_id=sub)
        if not draw_summary_item:
            draw_summary_item = DrawSummaryLineItem()
            draw_summary_item.draw_id = draw
            draw_summary_item.sub_id = sub
            draw_summary_item.draw_amount = sub_draw_items[sub.id]['sum']
            draw_summary_item.description = "Description"

            exhibits = Exhibit.objects.filter(sub_id=sub)
            contractTotal = 0
            totalPaid = 0
            for exhibit in exhibits:
                for line_item in ExhibitLineItem.objects.filter(exhibit_id=exhibit):
                    contractTotal += line_item.total
                    totalPaid += line_item.total_paid

            draw_summary_item.contract_total = contractTotal
            draw_summary_item.total_paid = totalPaid
            draw_summary_item.percent_complete = (totalPaid + draw_summary_item.draw_amount) / contractTotal * 100
            draw_summary_item.save()

    draw_summary_item = [model_to_dict(item) for item in DrawSummaryLineItem.objects.filter(draw_id=draw)]


    data = {
        'draw': model_to_dict(draw),
        'draw_items': draw_summary_item,  # Include the draw items and their sum for each subcontractor
        'subs': [model_to_dict(sub) for sub in subs],
        'checks': [model_to_dict(check) for check in checks],
    }

    print(data)

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
        'signed': lr.signed
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
        'date': check.date.isoformat(),
        'pdf': check.pdf.url if check.pdf else None,
    }

@csrf_exempt
def webhook_handler(request):
    if request.method == 'POST':
        # Process the webhook payload
        # You can use request.body or request.POST to get the data
        data = request.body
        # Perform necessary actions like pulling the repository
        # Here you might want to call a script or service
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'method not allowed'}, status=405)

