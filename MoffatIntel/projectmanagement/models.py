import json
import os
from django.db import models
from pathlib import Path

STATE_OPTIONS = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]

csi_data_path = os.path.join(Path(__file__).resolve().parent.parent, "projectmanagement/static/projectmanagement/data/master_format.json")
with open(csi_data_path, 'r') as file:
    csi_data = json.load(file)

CSI_DIVISIONS = csi_data

STATUS_OPTIONS = [("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")]

METHOD_OPTIONS = [("I", "Invoice"), ("E", "Exhibit"), ("P", "Purchase Order")]

LIEN_RELEASE_OPTIONS = [("F", "Final"), ("C", "Conditional"), ("N", "N/A")]

class Project(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    status = models.CharField(max_length=1, choices=[("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")])
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zip = models.IntegerField()

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

class Group(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

class Subgroup(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

class Report(models.Model):
    name = models.CharField(max_length=150)

class Subcontractor(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=11)
    email = models.EmailField()
    w9 = models.CharField(max_length=20)
    csi = models.CharField(max_length=6)
    def __str__(self):
        return self.name

    def get_long_csi(self):
        # Parse the CSI code
        division = self.csi[:2]
        section = self.csi[2:4]
        subsection = self.csi[4:6]

        # Traverse the CSI data
        description = ''
        current = csi_data.get(division, None)
        if current:
            description += current['name']
            current = current.get(section, None)
            if current:
                description += f" > {current['name']}"
                current = current.get(subsection, None)
                if current:
                    description += f" > {current['name']}"

        return description


class Vendor(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    cname = models.CharField(max_length=50, default="")
    cphone = models.CharField(max_length=11, default="")
    cemail = models.EmailField(default="")
    w9 = models.CharField(max_length=20)
    csi = models.CharField(max_length=6)

    def __str__(self):
        return self.name

    def get_long_csi(self):
        # Parse the CSI code
        division = self.csi[:2]
        section = self.csi[2:4]
        subsection = self.csi[4:6]

        # Traverse the CSI data
        description = ''
        current = csi_data.get(division, None)
        if current:
            description += current['name']
            current = current.get(section, None)
            if current:
                description += f" > {current['name']}"
                current = current.get(subsection, None)
                if current:
                    description += f" > {current['name']}"

        return description

class Plan(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='projectmanagement/plans/', default=None)

    def __str__(self):
        return self.name

class MasterEstimate(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateTimeField('Last Modified')
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, blank=True, null=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    total = models.FloatField(default=0.00)
    csi = models.CharField(max_length=6)
    pdf = models.FileField(upload_to='projectmanagement/estimates/', default=None)

    def __str__(self):
        return self.name

    def get_long_csi(self):
        # Parse the CSI code
        division = self.csi[:2]
        section = self.csi[2:4]
        subsection = self.csi[4:6]

        # Traverse the CSI data
        description = ''
        current = csi_data.get(division, None)
        if current:
            description += current['name']
            current = current.get(section, None)
            if current:
                description += f" > {current['name']}"
                current = current.get(subsection, None)
                if current:
                    description += f" > {current['name']}"

        return description

class MasterEstimateLineItem(models.Model):
    estimate_id = models.ForeignKey(MasterEstimate, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, blank=True, null=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    subgroup_id = models.ForeignKey(Subgroup, on_delete=models.CASCADE, blank=True, null=True)
    scope = models.CharField(max_length=500)
    qty = models.IntegerField(default=0)
    unit_price = models.FloatField(default=0)
    total = models.FloatField(default=0)

    def __str__(self):
        return self.scope
class Estimate(models.Model):
    master_estimate_id = models.ForeignKey(MasterEstimate, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    date = models.DateTimeField('Last Modified')
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, blank=True, null=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    total = models.FloatField(default=0.00)
    csi = models.CharField(max_length=6)
    pdf = models.FileField(upload_to='projectmanagement/estimates/', default=None)

    def __str__(self):
        return self.name

    def get_long_csi(self):
        # Parse the CSI code
        division = self.csi[:2]
        section = self.csi[2:4]
        subsection = self.csi[4:6]

        # Traverse the CSI data
        description = ''
        current = csi_data.get(division, None)
        if current:
            description += current['name']
            current = current.get(section, None)
            if current:
                description += f" > {current['name']}"
                current = current.get(subsection, None)
                if current:
                    description += f" > {current['name']}"

        return description

class EstimateLineItem(models.Model):
    estimate_id = models.ForeignKey(Estimate, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, blank=True, null=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    subgroup_id = models.ForeignKey(Subgroup, on_delete=models.CASCADE, blank=True, null=True)
    scope = models.CharField(max_length=500)
    qty = models.IntegerField(default=0)
    unit_price = models.FloatField(default=0)
    total = models.FloatField(default=0)

    def __str__(self):
        return self.scope

class SWO(models.Model):
    date = models.DateTimeField('Last Modified')
    description = models.CharField(max_length=200, default="")
    total = models.FloatField()
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='projectmanagement/SWOs')

    def __str__(self):
        return self.name


class Exhibit(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    total = models.FloatField(default=0.00)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='projectmanagement/exhibits/', default=None)

    def __str__(self):
        return self.name

class ExhibitLineItem(models.Model):
    exhibit_id = models.ForeignKey(Exhibit, on_delete=models.CASCADE)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    subgroup_id = models.ForeignKey(Subgroup, on_delete=models.CASCADE, blank=True, null=True)
    scope = models.CharField(max_length=500)
    qty = models.IntegerField(default=1)
    unit_price = models.FloatField()
    total = models.FloatField()
    total_paid = models.FloatField(default=0.00)
    def __str__(self):
        return self.scope

class Contract(models.Model):
    date = models.DateTimeField('Last Modified')
    description = models.CharField(max_length=200, default="")
    total = models.FloatField()
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='projectmanagement/contracts')

    def __str__(self):
        return self.pdf.name


class ChangeOrder(models.Model):
    order_number = models.CharField(max_length=50)
    date = models.DateTimeField('Order Date')
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    total = models.FloatField(default=0.00)
    pdf = models.FileField(upload_to='projectmanagement/change_orders')
    def __str__(self):
        return self.order_number

class DeductiveChangeOrder(models.Model):
    order_number = models.CharField(max_length=50)
    date = models.DateTimeField('Order Date')
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    total = models.FloatField(default=0.00)
    pdf = models.FileField(upload_to='projectmanagement/deductive_change_orders')

    def __str__(self):
        return self.order_number


class PurchaseOrder(models.Model):
    name = models.CharField(max_length=50)
    order_number = models.CharField(max_length=50)
    date = models.DateTimeField('Order Date')
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, null=True)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    total = models.FloatField(default=0.00)
    pdf = models.FileField(upload_to='projectmanagement/purchase_orders')
    def __str__(self):
        return self.name


class Draw(models.Model):
    date = models.DateTimeField('Last Modified')
    num = models.IntegerField(default=1)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    edited_by = models.CharField(max_length=20)
    start_date = models.DateTimeField('Start Date')
    submitted_date = models.DateTimeField('Submitted Date', default=None, null=True)

    def __str__(self):
        return str(self.id)

class DrawLineItem(models.Model):
    draw_id = models.ForeignKey(Draw, on_delete=models.CASCADE)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    exhibit_item_id = models.ForeignKey(ExhibitLineItem, on_delete=models.CASCADE)
    draw_amount = models.FloatField(default=0.00)
    description = models.CharField(max_length=250)

class DrawSummaryLineItem(models.Model):
    draw_id = models.ForeignKey(Draw, on_delete=models.CASCADE)
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    contract_total = models.FloatField(default=0.00)
    percent_complete = models.FloatField(default=0.00)
    draw_amount = models.FloatField(default=0.00)
    total_paid = models.FloatField(default=0.00)
    description = models.CharField(max_length=250)

class LienRelease(models.Model):
    date = models.DateTimeField('Created Date')
    draw_item_id = models.ForeignKey(DrawSummaryLineItem, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, default="C",
                                         choices=[("F", "Final"), ("C", "Conditional"), ("N", "N/A")])
    pdf = models.FileField(default=None, null=True, upload_to='projectmanagement/lien_releases')
    signed = models.BooleanField(default=False)

    def get_LR_type_display_long(self):
        for choice in self._meta.get_field("type").choices:
            if choice[0] == self.type:
                return choice[1]
        return ""

class Check(models.Model):
    date = models.DateTimeField('Last Modified')
    draw_item_id = models.ForeignKey(DrawSummaryLineItem, on_delete=models.CASCADE)
    check_date = models.DateTimeField('Check Date')
    check_num = models.CharField(max_length=12)
    pdf = models.FileField(default=None, null=True, upload_to='projectmanagement/checks/')

    def __str__(self):
        return self.check_num.__str__()