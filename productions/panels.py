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
