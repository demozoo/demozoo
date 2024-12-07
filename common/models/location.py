from django.db import models
from unidecode import unidecode


class LocationMixin(models.Model):
    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    @property
    def asciified_location(self):
        return self.location and unidecode(self.location)

    class Meta:
        abstract = True
