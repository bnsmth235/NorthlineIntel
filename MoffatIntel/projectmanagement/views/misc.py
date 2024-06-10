import json
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from ..models import Invoice
@login_required(login_url='projectmanagement:login')
def todo(request):
    invoices = Invoice.objects.order_by("-invoice_date").filter(signed=False)

    context = {
        'invoices': invoices
    }

    return render(request, 'misc/todo.html', context)

@login_required(login_url='projectmanagement:login')
def get_master_format(request):
    with open(os.path.join(Path(__file__).resolve().parent.parent, "static/projectmanagement/data/master_format.json"), 'r') as file:
        data = json.load(file)
    return JsonResponse(data)
