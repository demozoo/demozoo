from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from taggit.admin import TagAdmin
from treebeard.admin import TreeAdmin

from productions.models import Credit, EmulatorConfig, Production, ProductionType, Screenshot, SoundtrackLink


class ProductionTypeAdmin(TreeAdmin):
    pass


class CreditInline(admin.TabularInline):
    model = Credit
    raw_id_fields = ['nick']


class ScreenshotInline(admin.StackedInline):
    model = Screenshot


class SoundtrackLinkInline(admin.TabularInline):
    model = SoundtrackLink
    fk_name = 'production'
    raw_id_fields = ['soundtrack']


admin.site.register(ProductionType, ProductionTypeAdmin)
admin.site.register(
    Production,
    inlines=[CreditInline, ScreenshotInline, SoundtrackLinkInline],
    raw_id_fields=['author_nicks', 'author_affiliation_nicks'],
    search_fields=['title']
)

TagAdmin.inlines = []

admin.site.register(EmulatorConfig, raw_id_fields=['production'])
