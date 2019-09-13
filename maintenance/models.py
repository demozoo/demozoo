from django.db import models

class Exclusion(models.Model):
    record_id = models.IntegerField()
    report_name = models.CharField(max_length = 255)
