from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    last_edit_date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    address = models.CharField(max_length=200)


class Contract(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)

class Proposal(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)

class SWO(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)

class Exhibit(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    contract_id = models.ForeignKey(Contract, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)


    trade = models.CharField(max_length=100)
    subcontractor = models.CharField(max_length=100)


class Draw(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)

class Invoice(models.Model):
    draw_id = models.ForeignKey(Draw, on_delete=models.CASCADE)

    invoice_date = models.DateTimeField('Invoice Date')
    invoice_num = models.IntegerField(default=0)
    subcontractor = models.CharField(max_length=50)
    invoice_total = models.FloatField(0.00)
    description = models.TextField()
    lien_release_type = models.CharField(max_length= 20, choices=[("F","Final"),("C","Conditional"),("N","N/A")])
    w9 = models.CharField(max_length=20)
