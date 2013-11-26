from django.contrib import admin

from parties.models import PartySeries, Party, Competition, CompetitionPlacing


class CompetitionPlacingInline(admin.TabularInline):
	model = CompetitionPlacing
	raw_id_fields = ['production']


admin.site.register(PartySeries)
admin.site.register(Party, raw_id_fields=['invitations'])
admin.site.register(Competition, inlines=[CompetitionPlacingInline], list_select_related=True)
