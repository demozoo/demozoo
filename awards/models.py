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


class Category(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
