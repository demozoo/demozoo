import datetime
import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from comments.forms import CommentForm
from comments.models import Comment
from common.utils.ajax import request_is_ajax
from common.views import AjaxConfirmationView, UpdateFormView, writeable_site_required
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
from productions.models import Screenshot


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


@writeable_site_required
@login_required
def create(request):
    if request.method == "POST":
        party = Party()
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            form.log_creation(request.user)

            if request_is_ajax(request):
                return HttpResponse("OK: %s" % party.get_absolute_url(), content_type="text/plain")
            else:
                messages.success(request, "Party added")
                return redirect("party", party.id)
    else:
        form = PartyForm(
            initial={
                "name": request.GET.get("name"),
                "party_series_name": request.GET.get("party_series_name"),
                "scene_org_folder": request.GET.get("scene_org_folder"),
            }
        )

    title = "New party"
    return render(
        request,
        "parties/create.html",
        {
            "form": form,
            "party_series_names": [ps.name for ps in PartySeries.objects.all()],
            "title": title,
            "html_title": title,
            "action_url": reverse("new_party"),
        },
    )


@writeable_site_required
def edit(request, party_id):
    if not request.user.is_authenticated:
        # Instead of redirecting back to this edit form after login, redirect to the party page.
        # This is because the edit button pointing here is the only one a non-logged-in user sees,
        # so they may intend to edit something else on the party page.
        return redirect_to_login(reverse("party", args=[party_id]))

    party = get_object_or_404(Party, id=party_id)
    if request.method == "POST":
        form = EditPartyForm(
            request.POST, instance=party, initial={"start_date": party.start_date, "end_date": party.end_date}
        )
        if form.is_valid():
            party.start_date = form.cleaned_data["start_date"]
            party.end_date = form.cleaned_data["end_date"]
            form.save()
            form.log_edit(request.user)

            # if we now have a website entry but the PartySeries record doesn't, copy it over
            if party.website and not party.party_series.website:
                party.party_series.website = party.website
                party.party_series.save()

            messages.success(request, "Party updated")
            return redirect("party", party.id)
    else:
        form = EditPartyForm(instance=party, initial={"start_date": party.start_date, "end_date": party.end_date})

    title = f"Editing party: {party.name}"
    return render(
        request,
        "parties/edit.html",
        {
            "party": party,
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("edit_party", args=[party.id]),
            "submit_button_label": "Update party",
        },
    )


class EditNotesView(UpdateFormView):
    form_class = PartyEditNotesForm
    action_url_name = "party_edit_notes"

    def get_object(self):
        return get_object_or_404(Party, id=self.kwargs["party_id"])

    def can_edit(self, object):
        return self.request.user.is_staff

    def get_title(self):
        return "Editing notes for %s" % self.object.name


@writeable_site_required
@login_required
def edit_external_links(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    if request.method == "POST":
        formset = PartyExternalLinkFormSet(request.POST, instance=party)
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, "party_edit_external_links")

            # see if there's anything useful we can extract for the PartySeries record
            try:
                pouet_party_link = party.external_links.get(link_class="PouetParty")
                pouet_party_id = pouet_party_link.parameter.split("/")[0]
            except (PartyExternalLink.DoesNotExist, PartyExternalLink.MultipleObjectsReturned):
                pass
            else:
                PartySeriesExternalLink.objects.get_or_create(
                    party_series=party.party_series, link_class="PouetPartySeries", parameter=pouet_party_id
                )

            # look for a Twitter username which *does not* end in a number -
            # assume that ones with a number are year-specific
            for link in party.external_links.filter(link_class="TwitterAccount"):
                if not re.search(r"\d$", link.parameter):
                    PartySeriesExternalLink.objects.get_or_create(
                        party_series=party.party_series, link_class="TwitterAccount", parameter=link.parameter
                    )

            return HttpResponseRedirect(party.get_absolute_url())
    else:
        formset = PartyExternalLinkFormSet(instance=party)

    title = f"Editing external links for {party.name}"
    return render(
        request,
        "generic/edit_external_links.html",
        {
            "formset": formset,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_edit_external_links", args=[party.id]),
        },
    )


@writeable_site_required
@login_required
def edit_series_external_links(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)

    if request.method == "POST":
        formset = PartySeriesExternalLinkFormSet(request.POST, instance=party_series)
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, "party_series_edit_external_links")

            return HttpResponseRedirect(party_series.get_absolute_url())
    else:
        formset = PartySeriesExternalLinkFormSet(instance=party_series)

    title = f"Editing external links for {party_series.name}"
    return render(
        request,
        "generic/edit_external_links.html",
        {
            "formset": formset,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_edit_series_external_links", args=[party_series.id]),
        },
    )


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


@writeable_site_required
@login_required
def add_competition(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    competition = Competition(party=party)
    if request.method == "POST":
        form = CompetitionForm(request.POST, instance=competition)
        if form.is_valid():
            competition.shown_date = form.cleaned_data["shown_date"]
            form.save()
            form.log_creation(request.user)
            # TODO: party updated_at datestamps
            # party.updated_at = datetime.datetime.now()
            # party.save()

            return redirect("competition_edit", competition.id)
    else:
        form = CompetitionForm(
            instance=competition,
            initial={
                "shown_date": party.default_competition_date(),
            },
        )

    title = f"New competition for {party.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_add_competition", args=[party.id]),
            "submit_button_label": "Create",
        },
    )


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


@writeable_site_required
@login_required
def edit_invitations(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    initial_forms = [{"production": production} for production in party.invitations.all()]

    if request.method == "POST":
        formset = PartyInvitationFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            invitations = [
                prod_form.cleaned_data["production"].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms and "production" in prod_form.cleaned_data
            ]
            party.invitations.set(invitations)

            if formset.has_changed():
                invitation_titles = [prod.title for prod in invitations] or ["none"]
                invitation_titles = ", ".join(invitation_titles)
                Edit.objects.create(
                    action_type="edit_party_invitations",
                    focus=party,
                    description="Set invitations to %s" % invitation_titles,
                    user=request.user,
                )

            return HttpResponseRedirect(party.get_absolute_url())
    else:
        formset = PartyInvitationFormset(initial=initial_forms)

    title = f"Editing invitations for {party.name}"
    return render(
        request,
        "parties/edit_invitations.html",
        {
            "party": party,
            "formset": formset,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_edit_invitations", args=[party.id]),
            "submit_button_label": "Update invitations",
        },
    )


@writeable_site_required
@login_required
def edit_releases(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    initial_forms = [{"production": production} for production in party.releases.all()]

    if request.method == "POST":
        formset = PartyReleaseFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            releases = [
                prod_form.cleaned_data["production"].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms and "production" in prod_form.cleaned_data
            ]
            party.releases.set(releases)

            if formset.has_changed():
                release_titles = [prod.title for prod in releases] or ["none"]
                release_titles = ", ".join(release_titles)
                Edit.objects.create(
                    action_type="edit_party_releases",
                    focus=party,
                    description="Set releases to %s" % release_titles,
                    user=request.user,
                )

            return HttpResponseRedirect(party.get_absolute_url())
    else:
        formset = PartyReleaseFormset(initial=initial_forms)

    title = f"Editing releases for {party.name}"
    return render(
        request,
        "parties/edit_releases.html",
        {
            "party": party,
            "formset": formset,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_edit_releases", args=[party.id]),
            "submit_button_label": "Update releases",
        },
    )


@writeable_site_required
@login_required
def edit_competition(request, party_id, competition_id):
    return redirect("competition_edit", competition_id)


@writeable_site_required
@login_required
def edit_share_image(request, party_id):
    if not request.user.is_staff:
        return redirect("home")

    party = get_object_or_404(Party, id=party_id)
    if request.method == "POST":
        form = PartyShareImageForm(request.POST, request.FILES, instance=party)
        if form.is_valid():
            form.save()

            messages.success(request, "Social share image updated")
            return redirect("party", party.id)
    else:
        form = PartyShareImageForm(instance=party)

    return render(
        request,
        "parties/edit_share_image.html",
        {
            "party": party,
            "form": form,
        },
    )


@writeable_site_required
@login_required
def add_organiser(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    if request.method == "POST":
        form = PartyOrganiserForm(request.POST)
        if form.is_valid():
            releaser = form.cleaned_data["releaser_nick"].commit().releaser
            if releaser.locked and not request.user.is_staff:
                messages.error(
                    request,
                    format_html(
                        "The scener profile for {} is protected and cannot be added as an organiser. "
                        'If you wish to add this organiser, <a href="/forums/3/">let us know in this thread</a>.',
                        releaser.name,
                    ),
                )
            else:
                organiser = Organiser(releaser=releaser, party=party, role=form.cleaned_data["role"])
                organiser.save()
                description = "Added %s as organiser of %s" % (releaser.name, party.name)
                Edit.objects.create(
                    action_type="add_party_organiser",
                    focus=releaser,
                    focus2=party,
                    description=description,
                    user=request.user,
                )
            return HttpResponseRedirect(party.get_absolute_url() + "?editing=organisers")
    else:
        form = PartyOrganiserForm()

    title = f"Add organiser for {party.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("party_add_organiser", args=[party.id]),
            "submit_button_label": "Add organiser",
        },
    )


@writeable_site_required
@login_required
def edit_organiser(request, party_id, organiser_id):
    party = get_object_or_404(Party, id=party_id)
    organiser = get_object_or_404(Organiser, party=party, id=organiser_id)

    if request.method == "POST":
        if organiser.releaser.locked and not request.user.is_staff:
            raise PermissionDenied
        else:
            form = PartyOrganiserForm(
                request.POST,
                initial={
                    "releaser_nick": organiser.releaser.primary_nick,
                    "role": organiser.role,
                },
            )
            if form.is_valid():
                releaser = form.cleaned_data["releaser_nick"].commit().releaser
                if releaser.locked and not request.user.is_staff:
                    messages.error(
                        request,
                        format_html(
                            "The scener profile for {} is protected and cannot be added as an organiser. "
                            'If you wish to add this organiser, <a href="/forums/3/">let us know in this thread</a>.',
                            releaser.name,
                        ),
                    )
                    return HttpResponseRedirect(party.get_absolute_url() + "?editing=organisers")

                organiser.releaser = releaser
                organiser.role = form.cleaned_data["role"]
                organiser.save()
                form.log_edit(request.user, releaser, party)

                return HttpResponseRedirect(party.get_absolute_url() + "?editing=organisers")
    else:
        form = PartyOrganiserForm(
            initial={
                "releaser_nick": organiser.releaser.primary_nick,
                "role": organiser.role,
            }
        )

    if organiser.releaser.locked and not request.user.is_staff:
        return render(
            request,
            "parties/edit_organiser_protected.html",
            {
                "party": party,
                "organiser": organiser,
            },
        )
    else:
        title = f"Editing {organiser.releaser.name} as organiser of {party.name}"
        return render(
            request,
            "generic/form.html",
            {
                "form": form,
                "title": title,
                "html_title": title,
                "action_url": reverse("party_edit_organiser", args=[party.id, organiser.id]),
                "submit_button_label": "Save changes",
                "delete_url": reverse("party_remove_organiser", args=[party.id, organiser.id]),
                "delete_link_text": "Remove organiser",
            },
        )


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
