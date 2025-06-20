from django.contrib import admin

from maintenance.models import UntrustedLinkIdentifier


class UntrustedLinkIdentifierAdmin(admin.ModelAdmin):
    list_display=["url_part"]
    # Custom description in the admin interface
    fieldsets = (
        (None, {
            'fields': ('url_part',)
        }),
        ('Instructions', {
            'description': 'Add parts of URLs that you identify as untrsuted. "Untrusted links" report will use '
            'these to list untrusted production links',
            'fields': (),
        })
    )

admin.site.register(UntrustedLinkIdentifier, UntrustedLinkIdentifierAdmin)
