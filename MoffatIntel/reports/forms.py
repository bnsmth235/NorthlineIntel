from django import forms
from .models import Plan

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['pdf']
