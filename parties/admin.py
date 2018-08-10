from django.contrib import admin

from parties.models import PartySeries, Party, Competition, CompetitionPlacing


class CompetitionPlacingInline(admin.TabularInline):
	model = CompetitionPlacing
	raw_id_fields = ['production']


admin.site.register(PartySeries, search_fields=['name'])
admin.site.register(Party, raw_id_fields=['invitations', 'releases', 'share_screenshot'], search_fields=['name', 'party_series__name'])
admin.site.register(
	Competition,
	inlines=[CompetitionPlacingInline],
	list_select_related=True,
	search_fields=['name', 'party__name', 'party__party_series__name']
)
