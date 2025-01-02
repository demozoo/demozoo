import datetime
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from awards.models import Event
from comments.forms import CommentForm
from comments.models import Comment
from common.utils.pagination import PaginationControls, extract_query_params
from common.views import writeable_site_required
from demoscene.models import Edit
from demoscene.shortcuts import get_page
from productions.carousel import Carousel
from productions.forms import ProductionDownloadLinkFormSet
from productions.models import Byline, Production, ProductionType
from productions.panels import (
    AwardsPanel,
    CreditsPanel,
    DownloadsPanel,
    ExternalLinksPanel,
    FeaturedInPanel,
    InfoFilesPanel,
    PackContentsPanel,
    PackedInPanel,
    SoundtracksPanel,
    TagsPanel,
)


class IndexView(View):
    # subclasses provide supertype, filter_form_class, template, url_name

    def get(self, request):
        queryset = Production.objects.filter(supertype=self.supertype)

        order = request.GET.get("order", "date")
        asc = request.GET.get("dir", "desc") == "asc"

        queryset = apply_order(queryset, order, asc)

        form = self.filter_form_class(request.GET)

        if form.is_valid():
            if form.cleaned_data["platform"]:
                queryset = queryset.filter(platforms=form.cleaned_data["platform"])
            if form.cleaned_data["production_type"]:
                prod_types = ProductionType.get_tree(form.cleaned_data["production_type"])
                queryset = queryset.filter(types__in=prod_types)

        queryset = queryset.prefetch_related(
            "author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types"
        )

        production_page = get_page(queryset, request.GET.get("page", "1"))

        return render(
            request,
            self.template,
            {
                "order": order,
                "production_page": production_page,
                "menu_section": "productions",
                "asc": asc,
                "form": form,
                "pagination_controls": PaginationControls(
                    production_page,
                    reverse(self.url_name),
                    extract_query_params(request.GET, ["order", "dir"] + list(form.fields.keys())),
                ),
            },
        )


def apply_order(queryset, order, asc):
    if order == "title":
        return queryset.order_by("%ssortable_title" % ("" if asc else "-"))
    elif order == "added":
        return queryset.order_by("%screated_at" % ("" if asc else "-"))
    else:  # date
        if asc:
            return queryset.order_by("release_date_date", "title")
        else:
            # fiddle order so that empty release dates end up at the end
            return queryset.extra(
                select={"order_date": "coalesce(productions_production.release_date_date, '1970-01-01')"}
            ).order_by("-order_date", "-title")


class ShowView(View):
    # subclasses provide supertype

    def get(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)
        if self.production.supertype != self.supertype:
            return HttpResponseRedirect(self.production.get_absolute_url())

        return render(self.request, "productions/show.html", self.get_context_data())

    def get_context_data(self):
        if self.request.user.is_authenticated:
            comment = Comment(commentable=self.production, user=self.request.user)
            comment_form = CommentForm(instance=comment, prefix="comment")

            awards_accepting_recommendations = [
                (event, event.get_recommendation_options(self.request.user, self.production))
                for event in Event.accepting_recommendations_for(self.production)
            ]
        else:
            comment_form = None

            awards_accepting_recommendations = [
                (event, None) for event in Event.accepting_recommendations_for(self.production)
            ]

        try:
            meta_screenshot = random.choice(self.production.screenshots.exclude(standard_url=""))
        except IndexError:
            meta_screenshot = None

        prompt_to_edit = settings.SITE_IS_WRITEABLE and (self.request.user.is_staff or not self.production.locked)
        can_edit = prompt_to_edit and self.request.user.is_authenticated

        primary_panels = [
            AwardsPanel(self.production),
            DownloadsPanel(self.production, self.request.user),
            InfoFilesPanel(self.production, self.request.user),
            ExternalLinksPanel(self.production, self.request.user),
            TagsPanel(self.production, self.request.user),
        ]

        credits_panel = CreditsPanel(
            production=self.production,
            user=self.request.user,
            is_editing=(self.request.GET.get("editing") == "credits"),
        )
        pack_contents_panel = PackContentsPanel(self.production, self.request.user)
        featured_in_panel = FeaturedInPanel(self.production)
        packed_in_panel = PackedInPanel(self.production)
        soundtracks_panel = SoundtracksPanel(self.production, self.request.user)

        secondary_panels = [
            credits_panel,
            pack_contents_panel,
            packed_in_panel,
            featured_in_panel,
            soundtracks_panel,
        ]

        show_secondary_panels = any(panel.is_shown for panel in secondary_panels)

        return {
            "production": self.production,
            "prompt_to_edit": prompt_to_edit,
            "can_edit": can_edit,
            "primary_panels": primary_panels,
            "secondary_panels": secondary_panels,
            "carousel": Carousel(self.production, self.request.user),
            "blurbs": self.production.blurbs.all() if self.request.user.is_staff else None,
            "comment_form": comment_form,
            "meta_screenshot": meta_screenshot,
            "awards_accepting_recommendations": awards_accepting_recommendations,
            "show_secondary_panels": show_secondary_panels,
        }


class HistoryView(View):
    # subclasses provide supertype

    def get(self, request, production_id):
        production = get_object_or_404(Production, id=production_id)
        if production.supertype != self.supertype:
            return HttpResponseRedirect(production.urls["history"])
        return render(
            request,
            "productions/history.html",
            {
                "production": production,
                "edits": Edit.for_model(production, request.user.is_staff),
            },
        )


class CreateView(View):
    # subclasses provide form_class, template, title, action_url_name, submit_button_label

    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request):
        if request.method == "POST":
            production = Production(updated_at=datetime.datetime.now())
            form = self.form_class(request.POST, instance=production)
            download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
            if form.is_valid() and download_link_formset.is_valid():
                form.save()
                download_link_formset.save_ignoring_uniqueness()
                form.log_creation(request.user)
                return HttpResponseRedirect(production.get_absolute_url())
        else:
            form = self.form_class(initial={"byline": Byline.from_releaser_id(request.GET.get("releaser_id"))})
            download_link_formset = ProductionDownloadLinkFormSet()
        return render(
            request,
            self.template,
            {
                "form": form,
                "download_link_formset": download_link_formset,
                "title": self.title,
                "html_title": self.title,
                "action_url": reverse(self.action_url_name),
                "submit_button_label": self.submit_button_label,
            },
        )
