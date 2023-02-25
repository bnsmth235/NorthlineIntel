from django.db import models

class Report(models.Model):
    title = models.CharField(max_length=200)
    request_date = models.DateTimeField('Date Requested')
    requested_by = models.CharField(max_length=20)
    status = models.BooleanField("Status")
