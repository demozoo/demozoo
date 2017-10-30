from __future__ import absolute_import  # ensure that 'from parties.foo' imports find the top-level parties module, not parties.views.parties

import json
import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Max

from demoscene.models import Edit
from demoscene.shortcuts import simple_ajax_confirmation
from productions.models import ProductionType, Production, Screenshot
from parties.models import Competition, CompetitionPlacing
from parties.forms import CompetitionForm
from platforms.models import Platform
from demoscene.utils import result_parser

from read_only_mode import writeable_site_required


def show(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)

	placings = competition.placings.order_by('position', 'production__id').prefetch_related('production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser').defer('production__notes', 'production__author_nicks__releaser__notes', 'production__author_affiliation_nicks__releaser__notes')
	entry_production_ids = [placing.production_id for placing in placings]
	screenshot_map = Screenshot.select_for_production_ids(entry_production_ids)
	placings = [
		(placing, screenshot_map.get(placing.production_id))
		for placing in placings
	]

	return render(request, 'competitions/show.html', {
		'competition': competition,
		'placings': placings,
	})


def history(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)
	return render(request, 'competitions/history.html', {
		'competition': competition,
		'edits': Edit.for_model(competition, request.user.is_staff),
	})


@writeable_site_required
@login_required
def edit(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)
	party = competition.party

	if request.method == 'POST':
		competition_form = CompetitionForm(request.POST, instance=competition)
		if competition_form.is_valid():
			competition.shown_date = competition_form.cleaned_data['shown_date']
			competition_form.save()
			competition_form.log_edit(request.user)
			return redirect('competition_edit', competition.id)
	else:
		competition_form = CompetitionForm(instance=competition, initial={
			'shown_date': competition.shown_date,
		})

	competition_placings = [placing.json_data for placing in competition.results()]

	competition_placings_json = json.dumps(competition_placings)

	platforms = Platform.objects.all()
	platforms_json = json.dumps([[p.id, p.name] for p in platforms])

	production_types = ProductionType.objects.all()
	production_types_json = json.dumps([[p.id, p.name] for p in production_types])

	competition_json = json.dumps({
		'id': competition.id,
		'platformId': competition.platform_id,
		'productionTypeId': competition.production_type_id,
	})

	return render(request, 'competitions/edit.html', {
		'form': competition_form,
		'party': party,
		'competition': competition,
		'competition_json': competition_json,
		'competition_placings_json': competition_placings_json,
		'platforms_json': platforms_json,
		'production_types_json': production_types_json,
		'is_admin': request.user.is_staff,
	})


@writeable_site_required
@login_required
def import_text(request, competition_id):
	if not request.user.is_staff:
		return redirect('competition_edit', competition_id)

	competition = get_object_or_404(Competition, id=competition_id)

	if request.POST:
		current_highest_position = CompetitionPlacing.objects.filter(competition=competition).aggregate(Max('position'))['position__max']
		next_position = (current_highest_position or 0) + 1

		format = request.POST['format']
		if format == 'tsv':
			rows = result_parser.tsv(request.POST['results'])
		elif format == 'pm1':
			rows = result_parser.partymeister_v1(request.POST['results'])
		elif format == 'pm2':
			rows = result_parser.partymeister_v2(request.POST['results'])
		elif format == 'wuhu':
			rows = result_parser.wuhu(request.POST['results'])
		else:
			return redirect('competition_edit', competition_id)

		for placing, title, byline, score in rows:
			if not title:
				continue

			production = Production(
				release_date=competition.shown_date,
				updated_at=datetime.datetime.now(),
				has_bonafide_edits=False,
				title=title)
			production.save()  # assign an ID so that associations work

			if competition.platform:
				production.platforms = [competition.platform]

			if competition.production_type:
				production.types = [competition.production_type]

			if byline:
				production.byline_string = byline

			production.supertype = production.inferred_supertype
			production.save()

			placing = CompetitionPlacing(
				production=production,
				competition=competition,
				ranking=placing,
				position=next_position,
				score=score,
			)
			next_position += 1
			placing.save()

			Edit.objects.create(action_type='add_competition_placing', focus=competition, focus2=production,
				description=(u"Added competition placing for %s in %s competition" % (production.title, competition)), user=request.user)

		return redirect('competition_edit', competition_id)
	else:
		return render(request, 'competitions/import_text.html', {
			'competition': competition,
		})


@writeable_site_required
@login_required
def delete(request, competition_id):
	competition = get_object_or_404(Competition, id=competition_id)

	if (not request.user.is_staff) or competition.placings.exists():
		return HttpResponseRedirect(competition.party.get_absolute_url())
	if request.method == 'POST':
		if request.POST.get('yes'):

			Edit.objects.create(action_type='delete_competition', focus=competition.party,
				description=(u"Deleted competition '%s'" % competition.name), user=request.user)

			competition.delete()

			messages.success(request, "%s competition deleted" % competition.name)
			return HttpResponseRedirect(competition.party.get_absolute_url())
		else:
			return HttpResponseRedirect(competition.party.get_absolute_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_competition', args=[competition_id]),
			"Are you sure you want to delete the %s competition?" % competition.name,
			html_title="Deleting %s" % competition.name)
