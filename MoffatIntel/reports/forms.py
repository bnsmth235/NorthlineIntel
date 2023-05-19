from django import forms
from .models import Plan, Invoice


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['pdf']


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_pdf']
