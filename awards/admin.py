from django.contrib import admin
from django.db import models

from awards.models import Category, Event, EventSeries, Juror, Nomination, PlatformGroup


class CategoryInline(admin.TabularInline):
    model = Category


class JurorInline(admin.TabularInline):
    model = Juror
    raw_id_fields = ["user"]


class NominationInline(admin.TabularInline):
    model = Nomination
    raw_id_fields = ["production"]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["event", "name", "nomination_count"]
    list_display_links = ["name"]
    ordering = ["event", "name"]
    fields = ["name"]
    inlines = [NominationInline]

    def nomination_count(self, obj):
        return obj.num_nominations

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(num_nominations=models.Count("nominations"))


class PlatformGroupInline(admin.TabularInline):
    model = PlatformGroup
    extra = 0


admin.site.register(EventSeries, inlines=[PlatformGroupInline])
admin.site.register(Event, inlines=[CategoryInline, JurorInline])
admin.site.register(Category, CategoryAdmin)
