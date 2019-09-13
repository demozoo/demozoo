from django.contrib import admin

from platforms.models import Platform, PlatformAlias


class PlatformAliasInline(admin.StackedInline):
    model = PlatformAlias

admin.site.register(Platform, inlines=[PlatformAliasInline], search_fields=['name'])
