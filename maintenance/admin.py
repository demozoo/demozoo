from django.contrib import admin

from maintenance.models import UnsafeLink

class UnsafeLinkAdmin(admin.ModelAdmin):
    list_display=["url_part"]
    # Custom description in the admin interface
    fieldsets = (
        (None, {
            'fields': ('url_part',)
        }),
        ('Instructions', {
            'description': 'Add parts of URLs that you identify as unsafe. "Unsafe links" report will use these to list'
            'unsafe production links',
            'fields': (),
        })
    )

admin.site.register(UnsafeLink, UnsafeLinkAdmin)
