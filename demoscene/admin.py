from django.contrib import admin

from demoscene.models import (
    Membership, Nick, NickVariant, Releaser, AccountProfile, CaptchaQuestion, TagDescription,
    BlacklistedTag
)


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


class NickVariantInline(admin.TabularInline):
    model = NickVariant
    verbose_name_plural = 'Variant spellings'


class NickInline(admin.StackedInline):
    model = Nick
    extra = 1


admin.site.register(Releaser,
    inlines=[NickInline, MemberOfInline, MembersInline],
    search_fields=['nicks__variants__name'])
admin.site.register(Nick, inlines=[NickVariantInline], raw_id_fields=['releaser'],
    search_fields=['variants__name'])
admin.site.register(AccountProfile)
admin.site.register(CaptchaQuestion)
admin.site.register(TagDescription, ordering=['tag__name'], search_fields=['tag__name'])
admin.site.register(BlacklistedTag, ordering=['tag'], search_fields=['tag'], list_display=('tag', 'replacement'))
