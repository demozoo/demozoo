# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Group(models.Model):
	pouet_id = models.IntegerField(unique=True, db_index=True)
	name = models.CharField(max_length=255)
	demozoo_id = models.IntegerField(null=True, blank=True)
	last_seen_at = models.DateTimeField()


class Production(models.Model):
	pouet_id = models.IntegerField(unique=True, db_index=True)
	name = models.CharField(max_length=255)
	groups = models.ManyToManyField(Group, related_name='productions')
	last_seen_at = models.DateTimeField()
