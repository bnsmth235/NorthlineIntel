from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Report)
admin.site.register(Draw)
admin.site.register(DrawLineItem)
admin.site.register(DrawSummaryLineItem)
admin.site.register(Plan)
admin.site.register(ChangeOrder)
admin.site.register(PurchaseOrder)
admin.site.register(Subcontractor)
admin.site.register(Group)
admin.site.register(Subgroup)
admin.site.register(Check)
admin.site.register(ExhibitLineItem)
admin.site.register(Estimate)
admin.site.register(LienRelease)
admin.site.register(MasterEstimate)
admin.site.register(EstimateLineItem)

