from django.contrib import admin

from maintenance.models import UnsafeLink


admin.site.register(UnsafeLink, list_display=["url_part"])
