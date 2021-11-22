from django.contrib import admin

from awards.models import Category, Event, Juror


class CategoryInline(admin.TabularInline):
    model = Category


class JurorInline(admin.TabularInline):
    model = Juror
    raw_id_fields = ['user']


admin.site.register(Event, inlines=[CategoryInline, JurorInline])
