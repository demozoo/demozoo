from django.conf import settings
from django.utils.functional import cached_property
from laces.components import Component


class CreditsPanel(Component):
    template_name = "productions/includes/credits_panel.html"

    def __init__(self, production, user, is_editing):
        self.production = production
        self.prompt_to_edit = settings.SITE_IS_WRITEABLE and (user.is_staff or not self.production.locked)
        self.can_edit = self.prompt_to_edit and user.is_authenticated
        self.is_editing = is_editing

    @cached_property
    def credits(self):
        return self.production.credits_for_listing()

    @cached_property
    def is_shown(self):
        return bool(self.credits)

    def get_context_data(self, parent_context):
        return {
            "is_shown": self.is_shown,
            "production": self.production,
            "credits": self.credits,
            "can_edit": self.can_edit,
            "is_editing": self.is_editing,
        }


class PackContentsPanel(Component):
    template_name = "productions/includes/pack_contents_panel.html"

    def __init__(self, production, user):
        self.production = production
        self.prompt_to_edit = settings.SITE_IS_WRITEABLE and (user.is_staff or not self.production.locked)
        self.can_edit = self.prompt_to_edit and user.is_authenticated

    @cached_property
    def pack_members(self):
        return [
            link.member
            for link in (
                self.production.pack_members.select_related("member").prefetch_related(
                    "member__author_nicks__releaser", "member__author_affiliation_nicks__releaser"
                )
            )
        ]

    @cached_property
    def is_shown(self):
        return self.production.can_have_pack_members()

    def get_context_data(self, parent_context):
        return {
            "is_shown": self.is_shown,
            "production": self.production,
            "pack_members": self.pack_members,
            "can_edit": self.can_edit,
        }
