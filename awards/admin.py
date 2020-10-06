# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from awards.models import Event, Category, Juror


class CategoryInline(admin.TabularInline):
    model = Category


class JurorInline(admin.TabularInline):
    model = Juror
    raw_id_fields = ['user']


admin.site.register(Event, inlines=[CategoryInline, JurorInline])
