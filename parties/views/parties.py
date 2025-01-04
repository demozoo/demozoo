import datetime
import json
import re
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.http import urlencode
from django.views import View

from comments.forms import CommentForm
from comments.models import Comment
from common.utils.ajax import request_is_ajax
from common.views import AjaxConfirmationView, EditingView, UpdateFormView, writeable_site_required
from demoscene.models import Edit
from parties.forms import (
    CompetitionForm,
    EditPartyForm,
    EditPartySeriesForm,
    PartyEditNotesForm,
    PartyExternalLinkFormSet,
    PartyForm,
    PartyInvitationFormset,
    PartyOrganiserForm,
    PartyReleaseFormset,
    PartySeriesEditNotesForm,
    PartySeriesExternalLinkFormSet,
    PartyShareImageForm,
)
from parties.models import (
    Competition,
    Organiser,
    Party,
    PartyExternalLink,
    PartySeries,
    PartySeriesExternalLink,
    ResultsFile,
)
from parties import calendar_feeds
from productions.models import Screenshot
from iso3166 import countries


def by_name(request):
    parties = Party.objects.order_by("party_series__name", "start_date_date", "name").select_related("party_series")
    return render(
        request,
        "parties/by_name.html",
        {
            "parties": parties,
        },
    )


def by_date(request, year=None):
    try:
        year = int(year)
    except TypeError:
        year = datetime.date.today().year

    years = Party.objects.dates("start_date_date", "year") | Party.objects.dates("end_date_date", "year")

    parties = Party.objects.filter(start_date_date__year__lte=year, end_date_date__year__gte=year).order_by(
        "start_date_date", "end_date_date", "name"
    )

    return render(
        request,
        "parties/by_date.html",
        {
            "selected_year": year,
            "years": years,
            "parties": parties,
        },
    )


def show(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    competitions = party.get_competitions_with_prefetched_results()
    competitions_with_placings = [(competition, competition.placings.all()) for competition in competitions]
    entry_production_ids = [placing.production_id for _, placings in competitions_with_placings for placing in placings]
    screenshot_map = Screenshot.select_for_production_ids(entry_production_ids)
    competitions_with_placings_and_screenshots = [
        (competition, [(placing, screenshot_map.get(placing.production_id)) for placing in placings])
        for competition, placings in competitions_with_placings
    ]

    invitations = party.invitations.order_by("release_date_date").prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types"
    )

    releases = party.releases.prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types"
    )

    organisers = party.organisers.select_related("releaser").order_by("-releaser__is_group", Lower("releaser__name"))

    external_links = sorted(party.active_external_links.select_related("party"), key=lambda obj: obj.sort_key)

    tournaments = party.tournaments.order_by("name").prefetch_related(
        "phases__entries__nick__releaser", "phases__staff__nick__releaser"
    )

    if request.user.is_authenticated:
        comment = Comment(commentable=party, user=request.user)
        comment_form = CommentForm(instance=comment, prefix="comment")
    else:
        comment_form = None

    return render(
        request,
        "parties/show.html",
        {
            "party": party,
            "competitions_with_placings_and_screenshots": competitions_with_placings_and_screenshots,
            "tournaments": tournaments,
            "results_files": party.results_files.all(),
            "invitations": invitations,
            "releases": releases,
            "organisers": organisers,
            "editing_organisers": (request.GET.get("editing") == "organisers"),
            "parties_in_series": (
                party.party_series.parties.order_by("start_date_date", "name").select_related("party_series")
            ),
            "external_links": external_links,
            "comment_form": comment_form,
            "prompt_to_edit": settings.SITE_IS_WRITEABLE,
            "can_edit": settings.SITE_IS_WRITEABLE and request.user.is_authenticated,
        },
    )


def history(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    return render(
        request,
        "parties/history.html",
        {
            "party": party,
            "edits": Edit.for_model(party, request.user.is_staff),
        },
    )


def show_series(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)
    external_links = sorted(
        party_series.active_external_links.select_related("party_series"),
        key=lambda obj: obj.sort_key,
    )
    return render(
        request,
        "parties/show_series.html",
        {
            "party_series": party_series,
            "external_links": external_links,
            "parties": party_series.parties.order_by("start_date_date", "name"),
            "prompt_to_edit": settings.SITE_IS_WRITEABLE,
            "can_edit": settings.SITE_IS_WRITEABLE and request.user.is_authenticated,
            "new_edition_url": f"{reverse('new_party')}?{urlencode({'party_series_name':party_series.name})}",
        },
    )


def series_history(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)
    return render(
        request,
        "parties/series_history.html",
        {
            "party_series": party_series,
            "edits": Edit.for_model(party_series, request.user.is_staff),
        },
    )

class CountryLocation:
    country_re = re.compile('^[A-Z]{2,3}$')
    def __init__(self, country_code):
        if CountryLocation.country_re.match(country_code):
            self.country_code = country_code
        else:
            self.country_code = ''
        try:
            self.location = countries.get(country_code).name
        except:
            self.location = 'Unknown'

def ical_feed_url(request):
    is_ajax = request_is_ajax(request)

    country_feeds = []
    if not is_ajax:
        known_countries = Party.objects.exclude(country_code="").values_list("country_code", flat=True).order_by("country_code").distinct()
        known_countries = sorted(
            [CountryLocation(code) for code in known_countries],
            key=lambda c: c.location,
        )
        for country in known_countries:
            country_feeds.append({
                'location': country,
                'url':request.build_absolute_uri(reverse(country_ical_feed, kwargs={'code':country.country_code})),
            })

    return render(
        request,
        "parties/ical_feed_url.html",
        {
            "feed_url": request.build_absolute_uri(reverse(ical_feed)),
            "historical_feed_url": request.build_absolute_uri(reverse(historical_ical_feed)),
            "other_feeds_url": request.build_absolute_uri(reverse(ical_feed_url)),
            "online_only_url":request.build_absolute_uri(reverse(online_ical_feed)),
            "country_feeds": country_feeds,
            "is_ajax": is_ajax,
        },
    )

def handle_ical_request(request, path):
    return HttpResponse(
        calendar_feeds.get_feed(path, request.build_absolute_uri('/')),
        headers={
            "Content-Type": "text/calendar"
        },
    )

def ical_feed(request):
    return handle_ical_request(request, 'main')

def historical_ical_feed(request):
    return handle_ical_request(request, 'historical')

def online_ical_feed(request):
    return handle_ical_request(request, 'online_only')

def country_ical_feed(request, code):
    path = os.path.join('country', code)
    return handle_ical_request(request, path)


class CreateView(EditingView):
    title = "New party"
    template_name = "parties/create.html"

    def post(self, request):
        party = Party()
        self.form = PartyForm(request.POST, instance=party)
        if self.form.is_valid():
            self.form.save()
            self.form.log_creation(request.user)

            if request_is_ajax(request):
                return HttpResponse("OK: %s" % party.get_absolute_url(), content_type="text/plain")
            else:
                messages.success(request, "Party added")
                return redirect("party", party.id)
        else:
            return self.render_to_response()

    def get(self, request):
        self.form = PartyForm(
            initial={
                "name": request.GET.get("name"),
                "party_series_name": request.GET.get("party_series_name"),
                "scene_org_folder": request.GET.get("scene_org_folder"),
            }
        )
        return self.render_to_response()

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "party_series_names": [ps.name for ps in PartySeries.objects.all()],
                "action_url": reverse("new_party"),
            },
        )
        return context


class EditView(EditingView):
    template_name = "parties/edit.html"

    def get_login_return_url(self):
        # Instead of redirecting back to this edit form after login, redirect to the party page.
        # This is because the edit button pointing here is the only one a non-logged-in user sees,
        # so they may intend to edit something else on the party page.
        return reverse("party", args=[self.kwargs["party_id"]])

    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)

    def post(self, request, party_id):
        self.form = EditPartyForm(
            request.POST,
            instance=self.party,
            initial={"start_date": self.party.start_date, "end_date": self.party.end_date},
        )
        if self.form.is_valid():
            self.party.start_date = self.form.cleaned_data["start_date"]
            self.party.end_date = self.form.cleaned_data["end_date"]
            self.form.save()
            self.form.log_edit(request.user)

            # if we now have a website entry but the PartySeries record doesn't, copy it over
            if self.party.website and not self.party.party_series.website:
                self.party.party_series.website = self.party.website
                self.party.party_series.save()

            messages.success(request, "Party updated")
            return redirect("party", self.party.id)
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.form = EditPartyForm(
            instance=self.party, initial={"start_date": self.party.start_date, "end_date": self.party.end_date}
        )
        return self.render_to_response()

    def get_title(self):
        return f"Editing party: {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "party": self.party,
                "form": self.form,
                "action_url": reverse("edit_party", args=[self.party.id]),
                "submit_button_label": "Update party",
            },
        )
        return context


class EditNotesView(UpdateFormView):
    form_class = PartyEditNotesForm
    action_url_name = "party_edit_notes"

    def get_object(self):
        return get_object_or_404(Party, id=self.kwargs["party_id"])

    def can_edit(self, object):
        return self.request.user.is_staff

    def get_title(self):
        return "Editing notes for %s" % self.object.name


class EditExternalLinksView(EditingView):
    template_name = "generic/edit_external_links.html"

    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)

    def post(self, request, party_id):
        self.formset = PartyExternalLinkFormSet(request.POST, instance=self.party)
        if self.formset.is_valid():
            self.formset.save_ignoring_uniqueness()
            self.formset.log_edit(request.user, "party_edit_external_links")

            # see if there's anything useful we can extract for the PartySeries record
            try:
                pouet_party_link = self.party.external_links.get(link_class="PouetParty")
                pouet_party_id = pouet_party_link.parameter.split("/")[0]
            except (PartyExternalLink.DoesNotExist, PartyExternalLink.MultipleObjectsReturned):
                pass
            else:
                PartySeriesExternalLink.objects.get_or_create(
                    party_series=self.party.party_series, link_class="PouetPartySeries", parameter=pouet_party_id
                )

            # look for a Twitter username which *does not* end in a number -
            # assume that ones with a number are year-specific
            for link in self.party.external_links.filter(link_class="TwitterAccount"):
                if not re.search(r"\d$", link.parameter):
                    PartySeriesExternalLink.objects.get_or_create(
                        party_series=self.party.party_series, link_class="TwitterAccount", parameter=link.parameter
                    )

            return HttpResponseRedirect(self.party.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.formset = PartyExternalLinkFormSet(instance=self.party)
        return self.render_to_response()

    def get_title(self):
        return f"Editing external links for {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "formset": self.formset,
                "action_url": reverse("party_edit_external_links", args=[self.party.id]),
            },
        )
        return context


class EditSeriesExternalLinksView(EditingView):
    template_name = "generic/edit_external_links.html"

    def prepare(self, request, party_series_id):
        self.party_series = get_object_or_404(PartySeries, id=party_series_id)

    def post(self, request, party_series_id):
        self.formset = PartySeriesExternalLinkFormSet(request.POST, instance=self.party_series)
        if self.formset.is_valid():
            self.formset.save_ignoring_uniqueness()
            self.formset.log_edit(request.user, "party_series_edit_external_links")

            return HttpResponseRedirect(self.party_series.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, party_series_id):
        self.formset = PartySeriesExternalLinkFormSet(instance=self.party_series)
        return self.render_to_response()

    def get_title(self):
        return f"Editing external links for {self.party_series.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "formset": self.formset,
                "action_url": reverse("party_edit_series_external_links", args=[self.party_series.id]),
            },
        )
        return context


class EditSeriesNotesView(UpdateFormView):
    form_class = PartySeriesEditNotesForm
    action_url_name = "party_edit_series_notes"

    def get_object(self):
        return get_object_or_404(PartySeries, id=self.kwargs["party_series_id"])

    def can_edit(self, object):
        return self.request.user.is_staff

    def get_title(self):
        return "Editing notes for %s" % self.object.name


class EditSeriesView(UpdateFormView):
    form_class = EditPartySeriesForm
    action_url_name = "party_edit_series"

    def get_object(self):
        return get_object_or_404(PartySeries, id=self.kwargs["party_series_id"])

    def get_title(self):
        return "Editing party: %s" % self.object.name

    def get_login_return_url(self):
        # Instead of redirecting back to this edit form after login, redirect to the party series page.
        # This is because the edit button pointing here is the only one a non-logged-in user sees,
        # so they may intend to edit something else on the party series page.
        return reverse("party_series", args=[self.kwargs["party_series_id"]])


class AddCompetitionView(EditingView):
    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)
        self.competition = Competition(party=self.party)

    def post(self, request, party_id):
        self.form = CompetitionForm(request.POST, instance=self.competition)
        if self.form.is_valid():
            self.competition.shown_date = self.form.cleaned_data["shown_date"]
            self.form.save()
            self.form.log_creation(request.user)
            # TODO: party updated_at datestamps
            # self.party.updated_at = datetime.datetime.now()
            # self.party.save()

            return redirect("competition_edit", self.competition.id)
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.form = CompetitionForm(
            instance=self.competition,
            initial={
                "shown_date": self.party.default_competition_date(),
            },
        )
        return self.render_to_response()

    def get_title(self):
        return f"New competition for {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("party_add_competition", args=[self.party.id]),
                "submit_button_label": "Create",
            },
        )
        return context


def results_file(request, party_id, file_id):
    party = get_object_or_404(Party, id=party_id)
    results_file = get_object_or_404(ResultsFile, party=party, id=file_id)
    fix_encoding_url = (
        reverse("maintenance:fix_results_file_encoding", args=(file_id,))
        + "?"
        + urlencode({"return_to": reverse("party_results_file", args=(party_id, file_id))})
    )
    return render(
        request,
        "parties/results_file.html",
        {
            "party": party,
            "results_file": results_file,
            "fix_encoding_url": fix_encoding_url,
        },
    )


def autocomplete(request):
    query = request.GET.get("term")
    parties = Party.objects.filter(name__istartswith=query)
    parties = parties[:10]

    party_data = [
        {
            "id": party.id,
            "value": party.name,
        }
        for party in parties
    ]
    return HttpResponse(json.dumps(party_data), content_type="text/javascript")


class EditInvitationsView(EditingView):
    template_name = "parties/edit_invitations.html"

    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)
        self.initial_forms = [{"production": production} for production in self.party.invitations.all()]

    def post(self, request, party_id):
        self.formset = PartyInvitationFormset(request.POST, initial=self.initial_forms)
        if self.formset.is_valid():
            invitations = [
                prod_form.cleaned_data["production"].commit()
                for prod_form in self.formset.forms
                if prod_form not in self.formset.deleted_forms and "production" in prod_form.cleaned_data
            ]
            self.party.invitations.set(invitations)

            if self.formset.has_changed():
                invitation_titles = [prod.title for prod in invitations] or ["none"]
                invitation_titles = ", ".join(invitation_titles)
                Edit.objects.create(
                    action_type="edit_party_invitations",
                    focus=self.party,
                    description="Set invitations to %s" % invitation_titles,
                    user=request.user,
                )

            return HttpResponseRedirect(self.party.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.formset = PartyInvitationFormset(initial=self.initial_forms)
        return self.render_to_response()

    def get_title(self):
        return f"Editing invitations for {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "party": self.party,
                "formset": self.formset,
                "action_url": reverse("party_edit_invitations", args=[self.party.id]),
                "submit_button_label": "Update invitations",
            },
        )
        return context


class EditReleasesView(EditingView):
    template_name = "parties/edit_releases.html"

    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)
        self.initial_forms = [{"production": production} for production in self.party.releases.all()]

    def post(self, request, party_id):
        self.formset = PartyReleaseFormset(request.POST, initial=self.initial_forms)
        if self.formset.is_valid():
            releases = [
                prod_form.cleaned_data["production"].commit()
                for prod_form in self.formset.forms
                if prod_form not in self.formset.deleted_forms and "production" in prod_form.cleaned_data
            ]
            self.party.releases.set(releases)

            if self.formset.has_changed():
                release_titles = [prod.title for prod in releases] or ["none"]
                release_titles = ", ".join(release_titles)
                Edit.objects.create(
                    action_type="edit_party_releases",
                    focus=self.party,
                    description="Set releases to %s" % release_titles,
                    user=request.user,
                )

            return HttpResponseRedirect(self.party.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.formset = PartyReleaseFormset(initial=self.initial_forms)
        return self.render_to_response()

    def get_title(self):
        return f"Editing releases for {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "party": self.party,
                "formset": self.formset,
                "action_url": reverse("party_edit_releases", args=[self.party.id]),
                "submit_button_label": "Update releases",
            },
        )
        return context


@writeable_site_required
@login_required
def edit_competition(request, party_id, competition_id):
    return redirect("competition_edit", competition_id)


class EditShareImageView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, party_id):
        if not request.user.is_staff:
            return redirect("home")

        self.party = get_object_or_404(Party, id=party_id)

        return super().dispatch(request, party_id)

    def post(self, request, party_id):
        self.form = PartyShareImageForm(request.POST, request.FILES, instance=self.party)
        if self.form.is_valid():
            self.form.save()

            messages.success(request, "Social share image updated")
            return redirect("party", self.party.id)
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.form = PartyShareImageForm(instance=self.party)
        return self.render_to_response()

    def render_to_response(self):
        return render(
            self.request,
            "parties/edit_share_image.html",
            {
                "party": self.party,
                "form": self.form,
            },
        )


class AddOrganiserView(EditingView):
    def prepare(self, request, party_id):
        self.party = get_object_or_404(Party, id=party_id)

    def post(self, request, party_id):
        self.form = PartyOrganiserForm(request.POST)
        if self.form.is_valid():
            releaser = self.form.cleaned_data["releaser_nick"].commit().releaser
            if releaser.locked and not request.user.is_staff:
                messages.error(
                    request,
                    format_html(
                        "The scener profile for {} is protected and cannot be added as an organiser. "
                        "If you wish to add this organiser, "
                        '<a href="/forums/3/">let us know in this thread</a>.',
                        releaser.name,
                    ),
                )
            else:
                organiser = Organiser(releaser=releaser, party=self.party, role=self.form.cleaned_data["role"])
                organiser.save()
                description = "Added %s as organiser of %s" % (releaser.name, self.party.name)
                Edit.objects.create(
                    action_type="add_party_organiser",
                    focus=releaser,
                    focus2=self.party,
                    description=description,
                    user=request.user,
                )
            return HttpResponseRedirect(self.party.get_absolute_url() + "?editing=organisers")
        else:
            return self.render_to_response()

    def get(self, request, party_id):
        self.form = PartyOrganiserForm()
        return self.render_to_response()

    def get_title(self):
        return f"Add organiser for {self.party.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("party_add_organiser", args=[self.party.id]),
                "submit_button_label": "Add organiser",
            },
        )
        return context


class EditOrganiserView(EditingView):
    def prepare(self, request, party_id, organiser_id):
        self.party = get_object_or_404(Party, id=party_id)
        self.organiser = get_object_or_404(Organiser, party=self.party, id=organiser_id)

    def post(self, request, party_id, organiser_id):
        if self.organiser.releaser.locked and not request.user.is_staff:
            raise PermissionDenied
        else:
            self.form = PartyOrganiserForm(
                request.POST,
                initial={
                    "releaser_nick": self.organiser.releaser.primary_nick,
                    "role": self.organiser.role,
                },
            )
            if self.form.is_valid():
                releaser = self.form.cleaned_data["releaser_nick"].commit().releaser
                if releaser.locked and not request.user.is_staff:
                    messages.error(
                        request,
                        format_html(
                            "The scener profile for {} is protected and cannot be added as an organiser. "
                            "If you wish to add this organiser, "
                            '<a href="/forums/3/">let us know in this thread</a>.',
                            releaser.name,
                        ),
                    )
                    return HttpResponseRedirect(self.party.get_absolute_url() + "?editing=organisers")

                self.organiser.releaser = releaser
                self.organiser.role = self.form.cleaned_data["role"]
                self.organiser.save()
                self.form.log_edit(request.user, releaser, self.party)

                return HttpResponseRedirect(self.party.get_absolute_url() + "?editing=organisers")
            else:
                return self.render_to_response()

    def get(self, request, party_id, organiser_id):
        self.form = PartyOrganiserForm(
            initial={
                "releaser_nick": self.organiser.releaser.primary_nick,
                "role": self.organiser.role,
            }
        )
        return self.render_to_response()

    def get_title(self):
        return f"Editing {self.organiser.releaser.name} as organiser of {self.party.name}"

    def render_to_response(self):
        if self.organiser.releaser.locked and not self.request.user.is_staff:
            return render(
                self.request,
                "parties/edit_organiser_protected.html",
                {
                    "party": self.party,
                    "organiser": self.organiser,
                },
            )
        else:
            return super().render_to_response()

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("party_edit_organiser", args=[self.party.id, self.organiser.id]),
                "submit_button_label": "Save changes",
                "delete_url": reverse("party_remove_organiser", args=[self.party.id, self.organiser.id]),
                "delete_link_text": "Remove organiser",
            },
        )
        return context


class RemoveOrganiserView(AjaxConfirmationView):
    def get_object(self, request, party_id, organiser_id):
        self.party = Party.objects.get(id=party_id)
        self.organiser = Organiser.objects.get(party=self.party, id=organiser_id)
        if self.organiser.releaser.locked and not request.user.is_staff:
            raise PermissionDenied

    def get_redirect_url(self):
        return self.party.get_absolute_url() + "?editing=organisers"

    def get_action_url(self):
        return reverse("party_remove_organiser", args=[self.party.id, self.organiser.id])

    def get_message(self):
        return "Are you sure you want to remove %s as an organiser of %s?" % (
            self.organiser.releaser.name,
            self.party.name,
        )

    def get_html_title(self):
        return "Removing %s as organiser of %s" % (self.organiser.releaser.name, self.party.name)

    def perform_action(self):
        self.organiser.delete()
        description = "Removed %s as organiser of %s" % (self.organiser.releaser.name, self.party.name)
        Edit.objects.create(
            action_type="remove_party_organiser",
            focus=self.organiser.releaser,
            focus2=self.party,
            description=description,
            user=self.request.user,
        )
