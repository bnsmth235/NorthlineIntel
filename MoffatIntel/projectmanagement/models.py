from datetime import datetime

from django.db import models

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

DIVISION_CHOICES = [
    ("1", "General Requirement"),
    ("2", "Site Works"),
    ("3", "Concrete"),
    ("4", "Masonry"),
    ("5", "Metals"),
    ("6", "Wood and Plastics"),
    ("7", "Thermal and Moisture Protection"),
    ("8", "Doors and Windows"),
    ("9", "Finishes"),
    ("10", "Specialties"),
    ("11", "Equipment"),
    ("12", "Furnishings"),
    ("13", "Special Construction"),
    ("14", "Conveying Systems"),
    ("15", "Mechanical/Plumbing"),
    ("16", "Electrical"),
    ]

STATUS_OPTIONS = [("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")]

METHOD_OPTIONS = [("I", "Invoice"), ("E", "Exhibit"), ("P", "Purchase Order")]

LIEN_RELEASE_OPTIONS = [("F", "Final"), ("C", "Conditional"), ("N", "N/A")]


SUB_CATEGORIES = [
    ("1", "Civil Engineering"),
    ("2", "Architecture"),
    ("3", "Electrical Engineering"),
    ("4", "Mechanical Engineering"),
    ("5", "Plumbing"),
    ("6", "Environmental"),
    ("7", "Health Department"),
    ("8", "Amenities"),
    ("9", "Landscape"),
]
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
    name= models.CharField(max_length=20)

class Subgroup(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    name= models.CharField(max_length=20)

class Report(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateTimeField('Last run date')

class Subcontractor(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=11)
    email = models.EmailField()
    w9 = models.CharField(max_length=20)
    csi = models.CharField(max_length=2, choices=DIVISION_CHOICES)
    category = models.CharField(max_length=50, choices=SUB_CATEGORIES)
    def __str__(self):
        return self.name

    def get_long_csi(self):
        for choice in self._meta.get_field("csi").choices:
            if choice[0] == self.csi:
                return choice[1]
        return ""

    def get_long_category(self):
        for choice in self._meta.get_field("category").choices:
            if choice[0] == self.category:
                return choice[1]
        return ""


class Vendor(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    cname = models.CharField(max_length=50, default="")
    cphone = models.CharField(max_length=11, default="")
    cemail = models.EmailField(default="")
    w9 = models.CharField(max_length=20)
    csi = models.CharField(max_length=2, choices=DIVISION_CHOICES)
    category = models.CharField(max_length=50, choices=SUB_CATEGORIES)

    def __str__(self):
        return self.name

    def get_long_csi(self):
        for choice in self._meta.get_field("csi").choices:
            if choice[0] == self.csi:
                return choice[1]
        return ""

    def get_long_category(self):
        for choice in self._meta.get_field("category").choices:
            if choice[0] == self.category:
                return choice[1]
        return ""

class Plan(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Last Modified')
    edited_by = models.CharField(max_length=20)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to='projectmanagement/plans/', default=None)

    def __str__(self):
        return self.name


class Estimate(models.Model):
    date = models.DateTimeField('Last Modified')
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    total = models.FloatField(default=0.00)
    csi = models.CharField(max_length=2, choices=DIVISION_CHOICES)
    category = models.CharField(max_length=50, choices=SUB_CATEGORIES)
    pdf = models.FileField(upload_to='projectmanagement/estimates/', default=None)

    def __str__(self):
        return self.name

    def get_long_csi(self):
        for choice in self._meta.get_field("csi").choices:
            if choice[0] == self.csi:
                return choice[1]
        return ""

    def get_long_category(self):
        for choice in self._meta.get_field("category").choices:
            if choice[0] == self.category:
                return choice[1]
        return ""


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
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE)
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
    start_date = models.DateTimeField('Start Date', default=datetime.now())

    def __str__(self):
        return str(self.id)

class Invoice(models.Model):
    date = models.DateTimeField('Last Modified', default=datetime.now())
    draw_id = models.ForeignKey(Draw, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField('Invoice Date', default=datetime.now())
    invoice_num = models.CharField(default="", max_length=20)
    csi = models.CharField(max_length=50, choices=DIVISION_CHOICES)
    category = models.CharField(max_length=50, choices=SUB_CATEGORIES)
    method = models.CharField(max_length=1, default="I",
                              choices=[("I", "Invoice"), ("E", "Exhibit"), ("P", "Purchase Order")])
    sub_id = models.ForeignKey(Subcontractor, on_delete=models.CASCADE, blank=True, null=True)
    vendor_id = models.ForeignKey(Vendor, on_delete=models.CASCADE, blank=True, null=True)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    subgroup_id = models.ForeignKey(Subgroup, on_delete=models.CASCADE, blank=True, null=True)
    invoice_total = models.FloatField(default=0.00)
    description = models.TextField()
    invoice_pdf = models.FileField(default=None, upload_to='projectmanagement/invoices/')

    def __str__(self):
        return self.invoice_num

    def get_method_display_long(self):
        for choice in self._meta.get_field("method").choices:
            if choice[0] == self.method:
                return choice[1]
        return ""

    def get_sub_choices(self):
        # Retrieve the dynamic choices from the database or any other source
        # For example, you can query the Subcontractor model to get the choices
        subs = Subcontractor.objects.all()
        choices = [(sub.id, sub.name) for sub in subs]
        return choices

    def get_long_category(self):
        for choice in self._meta.get_field("category").choices:
            if choice[0] == self.category:
                return choice[1]
        return ""


class Check(models.Model):
    date = models.DateTimeField('Last Modified', default=datetime.now())
    invoice_id = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    check_date = models.DateTimeField('Check Date', default=datetime.now())
    check_num = models.IntegerField()
    check_total = models.FloatField(default=0.00)
    distributed = models.CharField(max_length=50)
    check_pdf = models.FileField(default=None, upload_to='projectmanagement/checks/')
    lien_release_type = models.CharField(max_length=20, default="N",
                                         choices=[("F", "Final"), ("C", "Conditional"), ("N", "N/A")])
    lien_release_pdf = models.FileField(default=None, upload_to='projectmanagement/lien_releases')
    signed = models.BooleanField(default=False)

    def __str__(self):
        return self.check_num.__str__()

    def get_LR_type_display_long(self):
        for choice in self._meta.get_field("lien_release_type").choices:
            if choice[0] == self.lien_release_type:
                return choice[1]
        return ""


