import datetime

from django.db import models
from django.forms import forms



class Project(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    status = models.CharField(max_length=1, choices=[("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")])
    address = models.CharField(max_length=200)

    @classmethod
    def create(cls, name, last_edit_date, edited_by, status, address):
        proj = cls(name=name, last_edit_date=last_edit_date, edited_by=edited_by, status=status, address=address)
        return proj

    def __str__(self):
        return self.name

    def get_status_display_long(self):
        for choice in self._meta.get_field("status").choices:
            if choice[0] == self.status:
                return choice[1]
        return ""


class Contract(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Subcontractor(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=11)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Plan(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='static/reports/plans/')

    def __str__(self):
        return self.name

class Proposal(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class SWO(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Exhibit(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)

    trade = models.CharField(max_length=100)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, default="")

    def __str__(self):
        return self.name


class Draw(models.Model):
    date = models.DateTimeField('Last Modified')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    edited_by = models.CharField(max_length=20)
    start_date = models.DateTimeField('Start Date', default=datetime.datetime.now())
    def __str__(self):
        return str(self.id)


class Invoice(models.Model):
    date = models.DateTimeField('Last Modified', default=datetime.datetime.now())
    draw_id = models.ForeignKey(Draw, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField('Invoice Date', default=datetime.datetime.now())
    invoice_num = models.CharField(default="", max_length=20)
    division_code = models.CharField(max_length=20)
    method = models.CharField(max_length=1, default="I", choices=[("I", "Invoice"), ("E", "Exhibit"), ("P", "Purchase Order")])
    sub = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    invoice_total = models.FloatField(default=0.00)
    description = models.TextField()
    lien_release_type = models.CharField(max_length=20, default="N", choices=[("F", "Final"), ("C", "Conditional"), ("N", "N/A")])
    w9 = models.CharField(max_length=20)
    invoice_pdf = models.FileField(default=None, upload_to='static/reports/invoices/')
    lien_release_pdf = models.FileField(default=None, upload_to='static/reports/lien_releases')

    def __str__(self):
        return self.invoice_num



    def get_sub_choices(self):
        # Retrieve the dynamic choices from the database or any other source
        # For example, you can query the Subcontractor model to get the choices
        subs = Subcontractor.objects.all()
        choices = [(sub.id, sub.name) for sub in subs]
        return choices