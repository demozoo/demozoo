from demoscene.shortcuts import *
from demoscene.models import Party, PartySeries, Competition, PartyExternalLink, ResultsFile, Production, Edit
from demoscene.forms.party import *

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json

import re

from unjoinify import unjoinify


def index(request):
	parties = Party.objects.order_by('party_series__name', 'start_date_date').select_related('party_series')
	return render(request, 'parties/index.html', {
		'parties': parties,
	})


def by_date(request):
	parties = Party.objects.order_by('start_date_date', 'end_date_date')
	return render(request, 'parties/by_date.html', {
		'parties': parties,
	})


def show(request, party_id):
	party = get_object_or_404(Party, id=party_id)

	columns = [
		'id',
		'name',
		'placings__id',
		'placings__ranking',
		'placings__score',
		'placings__production__id',
		'placings__production__title',
		'placings__production__supertype',
		'placings__production__unparsed_byline',
		'placings__production__author_nicks__id',
		'placings__production__author_nicks__name',
		'placings__production__author_nicks__releaser__id',
		'placings__production__author_nicks__releaser__is_group',
		'placings__production__author_affiliation_nicks__id',
		'placings__production__author_affiliation_nicks__name',
		'placings__production__author_affiliation_nicks__releaser__id',
		'placings__production__author_affiliation_nicks__releaser__is_group',
	]
	query = '''
		SELECT
			demoscene_competition.id AS id,
			demoscene_competition.name AS name,
			demoscene_competitionplacing.id AS placings__id,
			demoscene_competitionplacing.ranking AS placings__ranking,
			demoscene_competitionplacing.score AS placings__score,
			demoscene_production.id AS placings__production__id,
			demoscene_production.title AS placings__production__title,
			demoscene_production.supertype AS placings__production__supertype,
			demoscene_production.unparsed_byline AS placings__production__unparsed_byline,
			author_nick.id AS placings__production__author_nicks__id,
			author_nick.name AS placings__production__author_nicks__name,
			author.id AS placings__production__author_nicks__releaser__id,
			author.is_group AS placings__production__author_nicks__releaser__is_group,
			affiliation_nick.id AS placings__production__author_affiliation_nicks__id,
			affiliation_nick.name AS placings__production__author_affiliation_nicks__name,
			affiliation.id AS placings__production__author_affiliation_nicks__releaser__id,
			affiliation.is_group AS placings__production__author_affiliation_nicks__releaser__is_group
		FROM demoscene_competition
		LEFT JOIN demoscene_competitionplacing ON (demoscene_competition.id = demoscene_competitionplacing.competition_id)
		LEFT JOIN demoscene_production ON (demoscene_competitionplacing.production_id = demoscene_production.id)
		LEFT JOIN demoscene_production_author_nicks ON (demoscene_production_author_nicks.production_id = demoscene_production.id)
		LEFT JOIN demoscene_nick AS author_nick ON (demoscene_production_author_nicks.nick_id = author_nick.id)
		LEFT JOIN demoscene_releaser AS author ON (author_nick.releaser_id = author.id)
		LEFT JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production_author_affiliation_nicks.production_id = demoscene_production.id)
		LEFT JOIN demoscene_nick AS affiliation_nick ON (demoscene_production_author_affiliation_nicks.nick_id = affiliation_nick.id)
		LEFT JOIN demoscene_releaser AS affiliation ON (affiliation_nick.releaser_id = affiliation.id)
		WHERE demoscene_competition.party_id = %s
		ORDER BY
			demoscene_competition.name, demoscene_competition.id, demoscene_competitionplacing.position,
			demoscene_production.id, author_nick.id, affiliation_nick.id
	'''
	competitions = unjoinify(Competition, query, (party.id,), columns)

	# Do not show an invitations section in the special case that all invitations are
	# entries in a competition at this party (which probably means that it was an invitation compo)
	invitations = party.invitations.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')
	non_competing_invitations = invitations.exclude(competition_placings__competition__party=party)
	if not non_competing_invitations:
		invitations = Production.objects.none

	return render(request, 'parties/show.html', {
		'party': party,
		'competitions': competitions,
		'results_files': party.results_files.all(),
		'invitations': invitations,
	})


def history(request, party_id):
	party = get_object_or_404(Party, id=party_id)
	return render(request, 'parties/history.html', {
		'party': party,
		'edits': Edit.for_model(party),
	})


def show_series(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id=party_series_id)
	return render(request, 'parties/show_series.html', {
		'party_series': party_series,
	})


def series_history(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id=party_series_id)
	return render(request, 'parties/series_history.html', {
		'party_series': party_series,
		'edits': Edit.for_model(party_series),
	})


@login_required
def create(request):
	if request.method == 'POST':
		party = Party()
		form = PartyForm(request.POST, instance=party)
		if form.is_valid():
			form.save()
			form.log_creation(request.user)

			if request.is_ajax():
				return HttpResponse('OK: %s' % party.get_absolute_url(), mimetype='text/plain')
			else:
				messages.success(request, 'Party added')
				return redirect('party', args=[party.id])
	else:
		form = PartyForm(initial={
			'name': request.GET.get('name'),
			'party_series_name': request.GET.get('party_series_name'),
			'scene_org_folder': request.GET.get('scene_org_folder'),
		})
	return ajaxable_render(request, 'parties/create.html', {
		'html_title': "New party",
		'form': form,
		'party_series_names': [ps.name for ps in PartySeries.objects.all()],
	})


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
			return redirect('party', args=[party.id])
	else:
		form = EditPartyForm(instance=party, initial={
			'start_date': party.start_date,
			'end_date': party.end_date
		})

	return ajaxable_render(request, 'parties/edit.html', {
		'html_title': "Editing party: %s" % party.name,
		'party': party,
		'form': form,
	})


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


@login_required
def edit_external_links(request, party_id):
	party = get_object_or_404(Party, id=party_id)

	if request.method == 'POST':
		formset = PartyExternalLinkFormSet(request.POST, instance=party)
		if formset.is_valid():
			formset.save()
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
	return ajaxable_render(request, 'parties/edit_external_links.html', {
		'html_title': "Editing external links for %s" % party.name,
		'party': party,
		'formset': formset,
	})


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


@login_required
def edit_series(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id=party_series_id)

	def success(form):
		form.log_edit(request.user)

	return simple_ajax_form(request, 'party_edit_series', party_series, EditPartySeriesForm,
		title='Editing party: %s' % party_series.name, on_success=success
		#update_datestamp = True
	)


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
			if request.POST.get('enter_results'):
				return redirect('competition_edit', args=[competition.id])
			else:
				return HttpResponseRedirect(party.get_absolute_url())
	else:
		form = CompetitionForm(instance=competition, initial={
			'shown_date': party.default_competition_date(),
		})
	return ajaxable_render(request, 'parties/add_competition.html', {
		'html_title': "New competition for %s" % party.name,
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
	return HttpResponse(json.dumps(party_data), mimetype="text/javascript")


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
				if prod_form not in formset.deleted_forms]
			party.invitations = invitations

			if formset.has_changed():
				invitation_titles = [prod.title for prod in invitations] or ['none']
				invitation_titles = ", ".join(invitation_titles)
				Edit.objects.create(action_type='edit_party_invitations', focus=party,
					description=u"Set invitations to %s" % invitation_titles, user=request.user)

			return HttpResponseRedirect(party.get_absolute_url())
	else:
		formset = PartyInvitationFormset(initial=initial_forms)
	return ajaxable_render(request, 'parties/edit_invitations.html', {
		'html_title': "Editing invitations for %s" % party.name,
		'party': party,
		'formset': formset,
	})


@login_required
def edit_competition(request, party_id, competition_id):
	return redirect('competition_edit', args=[competition_id])
