# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255)
    eligibility_start_date = models.DateField(help_text="Earliest release date a production can have to be considered for these awards")
    eligibility_end_date = models.DateField(help_text="Latest release date a production can have to be considered for these awards")

    recommendations_enabled = models.BooleanField(default=False, help_text="Whether these awards are currently accepting recommendations")
    reporting_enabled = models.BooleanField(default=False, help_text="Whether jurors can currently view reports for these awards")

    def __unicode__(self):
        return self.name

    @classmethod
    def accepting_recommendations_for(cls, production):
        """
        Return a queryset of award events that it is currently possible
        to recommend this prod for
        """
        if production.supertype != 'production' or production.release_date_date is None:
            return cls.objects.none()

        return cls.objects.filter(
            recommendations_enabled=True,
            eligibility_start_date__lte=production.release_date_date,
            eligibility_end_date__gte=production.release_date_date,
        )


class Category(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
