from __future__ import absolute_import, unicode_literals

import datetime
import json
import re

from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from demoscene.shortcuts import simple_ajax_confirmation, simple_ajax_form
from demoscene.models import Edit
from productions.models import Screenshot
from parties.models import Organiser, Party, PartySeries, Competition, PartyExternalLink, ResultsFile
from parties.forms import (
    PartyForm, EditPartyForm, PartyEditNotesForm, PartyExternalLinkFormSet, PartyOrganiserForm,
    PartySeriesEditNotesForm, EditPartySeriesForm, CompetitionForm, PartyInvitationFormset, PartyReleaseFormset,
    PartyShareImageForm
)
from read_only_mode import writeable_site_required
from comments.models import Comment
from comments.forms import CommentForm


def by_name(request):
    parties = Party.objects.order_by('party_series__name', 'start_date_date', 'name').select_related('party_series')
    return render(request, 'parties/by_name.html', {
        'parties': parties,
    })


def by_date(request, year=None):
    try:
        year = int(year)
    except TypeError:
        year = datetime.date.today().year

    years = Party.objects.dates('start_date_date', 'year') | Party.objects.dates('end_date_date', 'year')

    parties = Party.objects.filter(
        start_date_date__year__lte=year, end_date_date__year__gte=year
    ).order_by('start_date_date', 'end_date_date', 'name')

    return render(request, 'parties/by_date.html', {
        'selected_year': year,
        'years': years,
        'parties': parties,
    })


def show(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    # trying to retrieve all competition results in one massive prefetch_related clause:
    #    competitions = party.competitions.prefetch_related('placings__production__author_nicks__releaser', 'placings__production__author_affiliation_nicks__releaser').defer('placings__production__notes', 'placings__production__author_nicks__releaser__notes', 'placings__production__author_affiliation_nicks__releaser__notes').order_by('name', 'id', 'placings__position', 'placings__production__id')
    # - fails with 'RelatedObject' object has no attribute 'rel', where the RelatedObject is <RelatedObject: demoscene:competitionplacing related to competition>. Shame, that...
    # for now, we'll do it one compo at a time (which allows us to use the slightly more sane select_related approach to pull in production records)
    competitions_with_placings = [
        (
            competition,
            competition.placings.order_by('position', 'production__id').prefetch_related('production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser', 'production__platforms', 'production__types').defer('production__notes', 'production__author_nicks__releaser__notes', 'production__author_affiliation_nicks__releaser__notes')
        )
        for competition in party.competitions.order_by('name', 'id')
    ]
    entry_production_ids = [
        placing.production_id
        for _, placings in competitions_with_placings
        for placing in placings
    ]
    screenshot_map = Screenshot.select_for_production_ids(entry_production_ids)
    competitions_with_placings_and_screenshots = [
        (
            competition,
            [(placing, screenshot_map.get(placing.production_id)) for placing in placings]
        )
        for competition, placings in competitions_with_placings
    ]

    invitations = party.invitations.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

    releases = party.releases.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

    organisers = party.organisers.select_related('releaser').order_by('-releaser__is_group', Lower('releaser__name'))

    external_links = sorted(party.active_external_links.select_related('party'), key=lambda obj: obj.sort_key)

    if request.user.is_authenticated:
        comment = Comment(commentable=party, user=request.user)
        comment_form = CommentForm(instance=comment, prefix="comment")
    else:
        comment_form = None

    return render(request, 'parties/show.html', {
        'party': party,
        'competitions_with_placings_and_screenshots': competitions_with_placings_and_screenshots,
        'results_files': party.results_files.all(),
        'invitations': invitations,
        'releases': releases,
        'organisers': organisers,
        'editing_organisers': (request.GET.get('editing') == 'organisers'),
        'parties_in_series': party.party_series.parties.order_by('start_date_date', 'name').select_related('party_series'),
        'external_links': external_links,
        'comment_form': comment_form,
    })


def history(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    return render(request, 'parties/history.html', {
        'party': party,
        'edits': Edit.for_model(party, request.user.is_staff),
    })


def show_series(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)
    return render(request, 'parties/show_series.html', {
        'party_series': party_series,
        'parties': party_series.parties.order_by('start_date_date', 'name')
    })


def series_history(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)
    return render(request, 'parties/series_history.html', {
        'party_series': party_series,
        'edits': Edit.for_model(party_series, request.user.is_staff),
    })


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        party = Party()
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            form.log_creation(request.user)

            if request.is_ajax():
                return HttpResponse('OK: %s' % party.get_absolute_url(), content_type='text/plain')
            else:
                messages.success(request, 'Party added')
                return redirect('party', party.id)
    else:
        form = PartyForm(initial={
            'name': request.GET.get('name'),
            'party_series_name': request.GET.get('party_series_name'),
            'scene_org_folder': request.GET.get('scene_org_folder'),
        })
    return render(request, 'parties/create.html', {
        'form': form,
        'party_series_names': [ps.name for ps in PartySeries.objects.all()],
    })


@writeable_site_required
@login_required
def edit(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    if request.method == 'POST':
        form = EditPartyForm(request.POST, instance=party, initial={
            'start_date': party.start_date,
            'end_date': party.end_date
        })
        if form.is_valid():
            party.start_date = form.cleaned_data['start_date']
            party.end_date = form.cleaned_data['end_date']
            form.save()
            form.log_edit(request.user)

            # if we now have a website entry but the PartySeries record doesn't, copy it over
            if party.website and not party.party_series.website:
                party.party_series.website = party.website
                party.party_series.save()

            messages.success(request, 'Party updated')
            return redirect('party', party.id)
    else:
        form = EditPartyForm(instance=party, initial={
            'start_date': party.start_date,
            'end_date': party.end_date
        })

    return render(request, 'parties/edit.html', {
        'party': party,
        'form': form,
    })


@writeable_site_required
@login_required
def edit_notes(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(party.get_absolute_edit_url())

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(request, 'party_edit_notes', party, PartyEditNotesForm,
        title='Editing notes for %s' % party.name, on_success=success,
        #update_datestamp = True
        )


@writeable_site_required
@login_required
def edit_external_links(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    if request.method == 'POST':
        formset = PartyExternalLinkFormSet(request.POST, instance=party)
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, 'party_edit_external_links')

            # see if there's anything useful we can extract for the PartySeries record
            party_series_updated = False
            if not party.party_series.pouet_party_id:
                try:
                    pouet_party_link = party.external_links.get(link_class='PouetParty')
                    party.party_series.pouet_party_id = pouet_party_link.parameter.split('/')[0]
                    party_series_updated = True
                except (PartyExternalLink.DoesNotExist, PartyExternalLink.MultipleObjectsReturned):
                    pass

            if not party.party_series.twitter_username:
                # look for a Twitter username which *does not* end in a number -
                # assume that ones with a number are year-specific
                twitter_usernames = []
                for link in party.external_links.filter(link_class='TwitterAccount'):
                    if not re.search(r'\d$', link.parameter):
                        twitter_usernames.append(link.parameter)

                if len(twitter_usernames) == 1:
                    party.party_series.twitter_username = twitter_usernames[0]
                    party_series_updated = True

            if party_series_updated:
                party.party_series.save()

            return HttpResponseRedirect(party.get_absolute_edit_url())
    else:
        formset = PartyExternalLinkFormSet(instance=party)
    return render(request, 'parties/edit_external_links.html', {
        'party': party,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_series_notes(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(party_series.get_absolute_edit_url())

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(request, 'party_edit_series_notes', party_series, PartySeriesEditNotesForm,
        title='Editing notes for %s' % party_series.name, on_success=success
        #update_datestamp = True
        )


@writeable_site_required
@login_required
def edit_series(request, party_series_id):
    party_series = get_object_or_404(PartySeries, id=party_series_id)

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(request, 'party_edit_series', party_series, EditPartySeriesForm,
        title='Editing party: %s' % party_series.name, on_success=success
        #update_datestamp = True
    )


@writeable_site_required
@login_required
def add_competition(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    competition = Competition(party=party)
    if request.method == 'POST':
        form = CompetitionForm(request.POST, instance=competition)
        if form.is_valid():
            competition.shown_date = form.cleaned_data['shown_date']
            form.save()
            form.log_creation(request.user)
            # TODO: party updated_at datestamps
            # party.updated_at = datetime.datetime.now()
            # party.save()

            return redirect('competition_edit', competition.id)
    else:
        form = CompetitionForm(instance=competition, initial={
            'shown_date': party.default_competition_date(),
        })
    return render(request, 'parties/add_competition.html', {
        'party': party,
        'form': form,
    })


def results_file(request, party_id, file_id):
    party = get_object_or_404(Party, id=party_id)
    results_file = get_object_or_404(ResultsFile, party=party, id=file_id)
    return render(request, 'parties/results_file.html', {
        'party': party,
        'text': results_file.text
    })


def autocomplete(request):
    query = request.GET.get('term')
    parties = Party.objects.filter(name__istartswith=query)
    parties = parties[:10]

    party_data = [
        {
            'id': party.id,
            'value': party.name,
        }
        for party in parties
    ]
    return HttpResponse(json.dumps(party_data), content_type="text/javascript")


@writeable_site_required
@login_required
def edit_invitations(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    initial_forms = [
        {'production': production}
        for production in party.invitations.all()
    ]

    if request.method == 'POST':
        formset = PartyInvitationFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            invitations = [prod_form.cleaned_data['production'].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms
                    and 'production' in prod_form.cleaned_data
            ]
            party.invitations.set(invitations)

            if formset.has_changed():
                invitation_titles = [prod.title for prod in invitations] or ['none']
                invitation_titles = ", ".join(invitation_titles)
                Edit.objects.create(action_type='edit_party_invitations', focus=party,
                    description=u"Set invitations to %s" % invitation_titles, user=request.user)

            return HttpResponseRedirect(party.get_absolute_url())
    else:
        formset = PartyInvitationFormset(initial=initial_forms)
    return render(request, 'parties/edit_invitations.html', {
        'party': party,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_releases(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    initial_forms = [
        {'production': production}
        for production in party.releases.all()
    ]

    if request.method == 'POST':
        formset = PartyReleaseFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            releases = [prod_form.cleaned_data['production'].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms
                    and 'production' in prod_form.cleaned_data
            ]
            party.releases.set(releases)

            if formset.has_changed():
                release_titles = [prod.title for prod in releases] or ['none']
                release_titles = ", ".join(release_titles)
                Edit.objects.create(action_type='edit_party_releases', focus=party,
                    description=u"Set releases to %s" % release_titles, user=request.user)

            return HttpResponseRedirect(party.get_absolute_url())
    else:
        formset = PartyReleaseFormset(initial=initial_forms)
    return render(request, 'parties/edit_releases.html', {
        'party': party,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_competition(request, party_id, competition_id):
    return redirect('competition_edit', competition_id)


@writeable_site_required
@login_required
def edit_share_image(request, party_id):
    if not request.user.is_staff:
        return redirect('home')

    party = get_object_or_404(Party, id=party_id)
    if request.method == 'POST':
        form = PartyShareImageForm(request.POST, request.FILES, instance=party)
        if form.is_valid():
            form.save()

            messages.success(request, 'Social share image updated')
            return redirect('party', party.id)
    else:
        form = PartyShareImageForm(instance=party)

    return render(request, 'parties/edit_share_image.html', {
        'party': party,
        'form': form,
    })


@writeable_site_required
@login_required
def add_organiser(request, party_id):
    party = get_object_or_404(Party, id=party_id)

    if request.method == 'POST':
        form = PartyOrganiserForm(request.POST)
        if form.is_valid():
            releaser = form.cleaned_data['releaser_nick'].commit().releaser
            organiser = Organiser(
                releaser=releaser,
                party=party,
                role=form.cleaned_data['role'])
            organiser.save()
            description = u"Added %s as organiser of %s" % (releaser.name, party.name)
            Edit.objects.create(action_type='add_party_organiser', focus=releaser, focus2=party,
                description=description, user=request.user)
            return HttpResponseRedirect(party.get_absolute_edit_url() + "?editing=organisers")
    else:
        form = PartyOrganiserForm()
    return render(request, 'parties/add_organiser.html', {
        'party': party,
        'form': form,
    })


@writeable_site_required
@login_required
def edit_organiser(request, party_id, organiser_id):
    party = get_object_or_404(Party, id=party_id)
    organiser = get_object_or_404(Organiser, party=party, id=organiser_id)

    if request.method == 'POST':
        form = PartyOrganiserForm(request.POST, initial={
            'releaser_nick': organiser.releaser.primary_nick,
            'role': organiser.role,
        })
        if form.is_valid():
            releaser = form.cleaned_data['releaser_nick'].commit().releaser
            organiser.releaser = releaser
            organiser.role = form.cleaned_data['role']
            organiser.save()
            form.log_edit(request.user, releaser, party)

            return HttpResponseRedirect(party.get_absolute_edit_url() + "?editing=organisers")
    else:
        form = PartyOrganiserForm(initial={
            'releaser_nick': organiser.releaser.primary_nick,
            'role': organiser.role,
        })
    return render(request, 'parties/edit_organiser.html', {
        'party': party,
        'organiser': organiser,
        'form': form,
    })


@writeable_site_required
@login_required
def remove_organiser(request, party_id, organiser_id):
    party = get_object_or_404(Party, id=party_id)
    organiser = get_object_or_404(Organiser, party=party, id=organiser_id)

    if request.method == 'POST':
        if request.POST.get('yes'):
            organiser.delete()
            description = u"Removed %s as organiser of %s" % (organiser.releaser.name, party.name)
            Edit.objects.create(action_type='remove_party_organiser', focus=organiser.releaser, focus2=party,
                description=description, user=request.user)
        return HttpResponseRedirect(party.get_absolute_edit_url() + "?editing=organisers")
    else:
        return simple_ajax_confirmation(request,
            reverse('party_remove_organiser', args=[party_id, organiser_id]),
            "Are you sure you want to remove %s as organiser of %s?" % (organiser.releaser.name, party.name),
            html_title="Removing %s as organiser of %s" % (organiser.releaser.name, party.name))
