from demoscene.shortcuts import *
from demoscene.models import Party, PartySeries, Competition, Platform, ProductionType, Production
from demoscene.forms.party import *

from django.contrib import messages
from django.contrib.auth.decorators import login_required

import re

from unjoinify import unjoinify

try:
	import json
except ImportError:
	import simplejson as json

def index(request):
	parties = Party.objects.order_by('party_series__name', 'start_date_date').select_related('party_series')
	return render(request, 'parties/index.html', {
		'parties': parties,
	})

def by_date(request):
	parties = Party.objects.order_by('start_date_date','end_date_date')
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
		'placings__production__author_nicks__id',
		'placings__production__author_nicks__name',
		'placings__production__author_nicks__releaser__id',
		'placings__production__author_nicks__releaser__is_group',
		'placings__production__author_affiliation_nicks__id',
		'placings__production__author_affiliation_nicks__name',
		'placings__production__author_affiliation_nicks__releaser__id',
		'placings__production__author_affiliation_nicks__releaser__is_group',
	]
	query ='''
		SELECT
			demoscene_competition.id AS id,
			demoscene_competition.name AS name,
			demoscene_competitionplacing.id AS placings__id,
			demoscene_competitionplacing.ranking AS placings__ranking,
			demoscene_competitionplacing.score AS placings__score,
			demoscene_production.id AS placings__production__id,
			demoscene_production.title AS placings__production__title,
			demoscene_production.supertype AS placings__production__supertype,
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
			demoscene_competition.name, demoscene_competitionplacing.position,
			demoscene_production.id, author_nick.id, affiliation_nick.id
	'''
	competitions = unjoinify(Competition, query, (party.id,), columns)

	return render(request, 'parties/show.html', {
		'party': party,
		'competitions': competitions,
	})

def show_series(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id=party_series_id)
	return render(request, 'parties/show_series.html', {
		'party_series': party_series,
	})

@login_required
def create(request):
	if request.method == 'POST':
		party = Party()
		form = PartyForm(request.POST, instance = party)
		if form.is_valid():
			try:
				party.party_series = PartySeries.objects.get(name = form.cleaned_data['party_series_name'])
			except PartySeries.DoesNotExist:
				ps = PartySeries(name = form.cleaned_data['party_series_name'])
				ps.save()
				party.party_series = ps
			
			party.start_date = form.cleaned_data['start_date']
			party.end_date = form.cleaned_data['end_date']
			
			# copy over usable fields from party_series
			if party.start_date:
				party.pouet_party_when = party.start_date.date.year
			if party.party_series.website:
				party.homepage = party.party_series.website
			if party.party_series.pouet_party_id:
				party.pouet_party_id = party.party_series.pouet_party_id
			if party.party_series.twitter_username:
				party.twitter_username = party.party_series.twitter_username
			
			form.save()
			messages.success(request, 'Party added')
			return redirect('party', args = [party.id])
	else:
		form = PartyForm()
	return render(request, 'parties/create.html', {
		'form': form,
		'party_series_names': [ps.name for ps in PartySeries.objects.all()],
	})

@login_required
def edit(request, party_id):
	party = get_object_or_404(Party, id = party_id)
	if request.method == 'POST':
		form = EditPartyForm(request.POST, instance = party)
		if form.is_valid():
			party.start_date = form.cleaned_data['start_date']
			party.end_date = form.cleaned_data['end_date']
			form.save()
			messages.success(request, 'Party updated')
			return redirect('party', args = [party.id])
	else:
		form = EditPartyForm(instance = party, initial = {
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
	party = get_object_or_404(Party, id = party_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(party.get_absolute_edit_url())
	return simple_ajax_form(request, 'party_edit_notes', party, PartyEditNotesForm,
		title = 'Editing notes for %s' % party.name,
		#update_datestamp = True
		)

@login_required
def edit_external_links(request, party_id):
	party = get_object_or_404(Party, id = party_id)
		
	if request.method == 'POST':
		form = PartyEditExternalLinksForm(request.POST, instance = party)
		if form.is_valid():
			form.save()
			# copy attributes to party_series if appropriate
			party_series_updated = False
			if party.party_series.pouet_party_id == None and party.pouet_party_id != None:
				party.party_series.pouet_party_id = party.pouet_party_id
				party_series_updated = True
			if party.homepage and not party.party_series.website:
				party.party_series.website = party.homepage
				party_series_updated = True
			if party.twitter_username and not party.party_series.twitter_username:
				if re.search(r'\d$', party.twitter_username):
					# twitter username ends in a number, so assume it's year-specific
					pass
				else:
					party.party_series.twitter_username = party.twitter_username
					party_series_updated = True
			if party_series_updated:
				party.party_series.save()
			return HttpResponseRedirect(party.get_absolute_edit_url())
	else:
		form = PartyEditExternalLinksForm(instance = party)
	
	return ajaxable_render(request, 'parties/edit_external_links.html', {
		'party': party,
		'form': form,
		'html_title': "Editing external links for %s" % party.name,
	})

@login_required
def edit_series_notes(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id = party_series_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(party_series.get_absolute_edit_url())
	return simple_ajax_form(request, 'party_edit_series_notes', party_series, PartySeriesEditNotesForm,
		title = 'Editing notes for %s' % party_series.name,
		#update_datestamp = True
		)

@login_required
def edit_series(request, party_series_id):
	party_series = get_object_or_404(PartySeries, id = party_series_id)
	return simple_ajax_form(request, 'party_edit_series', party_series, EditPartySeriesForm,
		title = 'Editing party: %s' % party_series.name,
		#update_datestamp = True
	)

@login_required
def add_competition(request, party_id):
	party = get_object_or_404(Party, id = party_id)
	competition = Competition(party = party)
	if request.method == 'POST':
		form = CompetitionForm(request.POST, instance = competition)
		if form.is_valid():
			form.save()
			# TODO: party updated_at datestamps
			# party.updated_at = datetime.datetime.now()
			# party.save()
			if request.POST.get('enter_results'):
				return redirect('party_edit_competition', args = [party.id, competition.id])
			else:
				return HttpResponseRedirect(party.get_absolute_url())
	else:
		form = CompetitionForm(instance = competition)
	return ajaxable_render(request, 'parties/add_competition.html', {
		'html_title': "New competition for %s" % party.name,
		'party': party,
		'form': form,
	})

@login_required
def edit_competition(request, party_id, competition_id):
	party = get_object_or_404(Party, id = party_id)
	competition = get_object_or_404(Competition, party = party, id = competition_id)
	if request.method == 'POST':
		competition_form = CompetitionForm(request.POST, instance = competition)
		formset = CompetitionPlacingFormset(request.POST, instance = competition)
		if competition_form.is_valid() and formset.is_valid():
			def form_order_key(form):
				if form.is_valid():
					return form.cleaned_data['ORDER'] or 9999
				else:
					return 9999
			
			sorted_forms = sorted(formset.forms, key = form_order_key)
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i+1
			formset.save()
			# TODO: competition/party updated_at datestamps
			#competition.updated_at = datetime.datetime.now()
			competition_form.save()
			return redirect('party', args = [party.id])
	else:
		competition_form = CompetitionForm(instance = competition)
		formset = CompetitionPlacingFormset(instance = competition)
	return ajaxable_render(request, 'parties/edit_competition.html', {
		'html_title': "Editing %s %s competition" % (party.name, competition.name),
		'party': party,
		'competition': competition,
		'formset': formset,
		'competition_form': competition_form,
	})

@login_required
def edit_competition_testing(request, party_id, competition_id):
	party = get_object_or_404(Party, id = party_id)
	competition = get_object_or_404(Competition, party = party, id = competition_id)
	
	results_with_forms = [
		(
			result,
			CompetitionResultForm(
				prefix='row_%s' % i,
				initial = {
					'placing': result.ranking,
					'title': result.production.title,
					'byline': result.production.byline(),
					'platform': result.production.platforms.all()[0].id if result.production.platforms.all() else None,
					'production_type': result.production.types.all()[0].id if result.production.types.all() else None,
					'score': result.score,
				},
			)
		)
		for (i, result) in enumerate(competition.results())
	]
	
	platforms = Platform.objects.all()
	platforms_json = json.dumps([ [p.id, p.name] for p in platforms ])
	
	production_types = ProductionType.objects.all()
	production_types_json = json.dumps([ [p.id, p.name] for p in production_types ])

	return ajaxable_render(request, 'parties/edit_competition_testing.html', {
		'html_title': "Editing %s %s competition" % (party.name, competition.name),
		'party': party,
		'competition': competition,
		'results_with_forms': results_with_forms,
		'platforms': platforms,
		'platforms_json': platforms_json,
		'production_types': production_types,
		'production_types_json': production_types_json,
	})
