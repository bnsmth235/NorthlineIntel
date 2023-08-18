from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from ..models import Invoice, Draw, Subcontractor, Project
@login_required(login_url='projectmanagement:login')
def todo(request):
    invoices = Invoice.objects.order_by("-invoice_date").filter(signed=False)

    context = {
        'invoices': invoices
    }

    return render(request, 'misc/todo.html', context)
