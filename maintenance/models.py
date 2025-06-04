from django.db import models


class Exclusion(models.Model):
    record_id = models.IntegerField()
    report_name = models.CharField(max_length=255)


class UnsafeLink(models.Model):
    url_part = models.CharField(max_length=64)

    def __str__(self):
        return self.url_part
