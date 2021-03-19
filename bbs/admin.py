from django.contrib import admin

from bbs.models import BBS, Affiliation, Operator


class StaffInline(admin.TabularInline):
    model = Operator
    raw_id_fields = ['releaser']


class AffiliationInline(admin.TabularInline):
    model = Affiliation
    raw_id_fields = ['group']


admin.site.register(BBS, raw_id_fields=['bbstros'], inlines=[StaffInline, AffiliationInline])
