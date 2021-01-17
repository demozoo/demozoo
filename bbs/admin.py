from django.contrib import admin

from bbs.models import BBS, Operator


class StaffInline(admin.TabularInline):
    model = Operator
    raw_id_fields = ['releaser']


admin.site.register(BBS, raw_id_fields=['bbstros'], inlines=[StaffInline])
