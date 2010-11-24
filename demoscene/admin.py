from django.contrib import admin
from treebeard.admin import TreeAdmin

from demoscene.models import *

class CompetitionPlacingInline(admin.TabularInline):
	model = CompetitionPlacing

class ProductionTypeAdmin(TreeAdmin):
	pass

admin.site.register(ProductionType, ProductionTypeAdmin)
admin.site.register(Platform)
admin.site.register(Production)
admin.site.register(Releaser)
admin.site.register(Nick)
admin.site.register(NickVariant)
admin.site.register(Credit)
admin.site.register(PartySeries)
admin.site.register(Party)
admin.site.register(Competition, inlines = [CompetitionPlacingInline])
admin.site.register(Screenshot)
admin.site.register(AccountProfile)
admin.site.register(SoundtrackLink)
