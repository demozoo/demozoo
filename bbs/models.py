from django.db import models

class BBS(models.Model):
    name = models.CharField(max_length=255)

    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'BBSes'
