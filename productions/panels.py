from django.conf import settings
from django.utils.functional import cached_property
from laces.components import Component

from productions.forms import ProductionTagsForm


class StaticPanel(Component):
    context_object_list_name = "object_list"

    def __init__(self, production):
        self.production = production

    def get_object_list(self):  # pragma: no cover
        return []

    @cached_property
    def object_list(self):
        return self.get_object_list()

    @cached_property
    def is_shown(self):
        return bool(self.object_list)

    def render_html(self, parent_context=None):
        if not self.is_shown:
            return ""
        return super().render_html(parent_context)

    def get_context_data(self, parent_context):
        return {
            self.context_object_list_name: self.object_list,
        }


class FeaturedInPanel(StaticPanel):
    template_name = "productions/includes/featured_in_panel.html"
    context_object_list_name = "featured_in_productions"

    def get_object_list(self):
        if self.production.supertype == "music":
            return [
                appearance.production
                for appearance in self.production.appearances_as_soundtrack.prefetch_related(
                    "production__author_nicks__releaser", "production__author_affiliation_nicks__releaser"
                ).order_by("production__release_date_date")
            ]
        else:
            return []


class PackedInPanel(StaticPanel):
    template_name = "productions/includes/packed_in_panel.html"
    context_object_list_name = "packed_in_productions"

    def get_object_list(self):
        return [
            pack_member.pack
            for pack_member in self.production.packed_in.prefetch_related(
                "pack__author_nicks__releaser", "pack__author_affiliation_nicks__releaser"
            ).order_by("pack__release_date_date")
        ]


class AwardsPanel(StaticPanel):
    template_name = "productions/includes/awards_panel.html"
    context_object_list_name = "award_nominations"

    def get_object_list(self):
        return (
            self.production.award_nominations.select_related("category", "category__event")
            .only("production__id", "category__name", "category__event__name", "category__event__id", "status")
            .order_by("category__event__name", "-status", "category__name")
        )


class EditablePanel(Component):
    context_object_list_name = "object_list"
    context_object_name = "production"
    # if render_hidden = True, the template will be rendered even when is_shown is False.
    # (Used for panels using the panel-refresh mechanism that may toggle between hidden and visible states)
    render_hidden = False

    def __init__(self, production, user, is_editing=False):
        self.production = production
        self.prompt_to_edit = settings.SITE_IS_WRITEABLE and (user.is_staff or not self.production.locked)
        self.can_edit = self.prompt_to_edit and user.is_authenticated
        self.is_editing = is_editing

    def get_object_list(self):  # pragma: no cover
        return []

    @cached_property
    def object_list(self):
        return self.get_object_list()

    @cached_property
    def is_shown(self):
        return bool(self.object_list)

    def render_html(self, parent_context=None):
        if not self.is_shown and not self.render_hidden:
            return ""
        return super().render_html(parent_context)

    def get_context_data(self, parent_context):
        return {
            self.context_object_name: self.production,
            self.context_object_list_name: self.object_list,
            "can_edit": self.can_edit,
            "is_shown": self.is_shown,
            "is_editing": self.is_editing,
        }


class CreditsPanel(EditablePanel):
    template_name = "productions/includes/credits_panel.html"
    context_object_list_name = "credits"
    render_hidden = True

    def get_object_list(self):
        return self.production.credits_for_listing()


class PackContentsPanel(EditablePanel):
    template_name = "productions/includes/pack_contents_panel.html"
    context_object_list_name = "pack_members"

    def get_object_list(self):
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


class SoundtracksPanel(EditablePanel):
    template_name = "productions/includes/soundtracks_panel.html"
    context_object_list_name = "soundtracks"
    render_hidden = True

    def get_object_list(self):
        if self.production.supertype == "production":
            return [
                link.soundtrack
                for link in self.production.soundtrack_links.order_by("position")
                .select_related("soundtrack")
                .prefetch_related(
                    "soundtrack__author_nicks__releaser", "soundtrack__author_affiliation_nicks__releaser"
                )
            ]
        else:
            return []


class DownloadsPanel(EditablePanel):
    template_name = "productions/includes/downloads_panel.html"
    context_object_list_name = "download_links"

    def get_object_list(self):
        return self.production.download_links


class ExternalLinksPanel(EditablePanel):
    template_name = "shared/external_links_panel.html"
    context_object_list_name = "external_links"
    context_object_name = "obj"

    def get_object_list(self):
        return self.production.external_links


class InfoFilesPanel(EditablePanel):
    template_name = "productions/includes/info_files_panel.html"
    context_object_list_name = "info_files"

    def get_object_list(self):
        return self.production.info_files.all()


class TagsPanel(EditablePanel):
    template_name = "productions/includes/tags_panel.html"
    context_object_list_name = "tags"

    def get_object_list(self):
        return self.production.tags.order_by("name")

    @cached_property
    def is_shown(self):
        return bool(self.object_list) or self.can_edit

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        if parent_context:
            context["csrf_token"] = parent_context.get("csrf_token")

        if self.can_edit:
            context["tags_form"] = ProductionTagsForm(instance=self.production)
        else:
            context["tags_form"] = None

        return context
