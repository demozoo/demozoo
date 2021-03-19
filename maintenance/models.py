from __future__ import absolute_import, unicode_literals

from django.db import models


class Exclusion(models.Model):
    record_id = models.IntegerField()
    report_name = models.CharField(max_length = 255)
