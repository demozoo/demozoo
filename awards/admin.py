# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from awards.models import Event, Category


class CategoryInline(admin.TabularInline):
    model = Category


admin.site.register(Event, inlines=[CategoryInline])
