from django.contrib import admin
from treebeard.admin import TreeAdmin

from demoscene.models import *


class MemberOfInline(admin.TabularInline):
	model = Membership
	fk_name = 'member'
	raw_id_fields = ['group']
	verbose_name_plural = 'Member of'


class MembersInline(admin.TabularInline):
	model = Membership
	fk_name = 'group'
	raw_id_fields = ['member']
	verbose_name_plural = 'Members'


class CreditInline(admin.TabularInline):
	model = Credit
	raw_id_fields = ['nick']


class ScreenshotInline(admin.StackedInline):
	model = Screenshot


class SoundtrackLinkInline(admin.TabularInline):
	model = SoundtrackLink
	fk_name = 'production'
	raw_id_fields = ['soundtrack']


class NickVariantInline(admin.TabularInline):
	model = NickVariant
	verbose_name_plural = 'Variant spellings'


class NickInline(admin.StackedInline):
	model = Nick
	extra = 1


class ProductionTypeAdmin(TreeAdmin):
	pass

admin.site.register(ProductionType, ProductionTypeAdmin)
admin.site.register(Production,
	inlines=[CreditInline, ScreenshotInline, SoundtrackLinkInline],
	raw_id_fields=['author_nicks', 'author_affiliation_nicks'],
	search_fields=['title'])
admin.site.register(Releaser,
	inlines=[NickInline, MemberOfInline, MembersInline],
	search_fields=['nicks__variants__name'])
admin.site.register(Nick, inlines=[NickVariantInline], raw_id_fields=['releaser'],
	search_fields=['variants__name'])
admin.site.register(AccountProfile)
admin.site.register(CaptchaQuestion)
admin.site.register(TagDescription, ordering=['tag__name'])
