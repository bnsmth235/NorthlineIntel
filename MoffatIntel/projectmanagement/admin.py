from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Draw)
admin.site.register(Plan)
admin.site.register(ChangeOrder)
admin.site.register(PurchaseOrder)
admin.site.register(Subcontractor)
admin.site.register(Group)
admin.site.register(Subgroup)
admin.site.register(Invoice)
admin.site.register(Check)

