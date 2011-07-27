from demoscene.shortcuts import *
from django.contrib.auth.decorators import login_required
from demoscene.models import Production, Nick, Credit
from django.db import connection, transaction
from fuzzy_date import FuzzyDate
from django.http import HttpResponseRedirect

def index(request):
	if not request.user.is_staff:
		return redirect('home')
	return render(request, 'maintenance/index.html')

def prods_without_screenshots(request):
	productions = Production.objects \
		.filter(screenshots__id__isnull = True) \
		.exclude(supertype = 'music').order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without screenshots',
		'productions': productions
	})

def prods_without_external_links(request):
	filters = {}
	for field in Production.external_site_ref_field_names:
		filters["%s__isnull" % field] = True
	
	productions = Production.objects \
		.filter(supertype = 'production', **filters) \
		.order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without external links',
		'productions': productions,
	})

def prods_without_release_date(request):
	productions = Production.objects.filter(release_date_date__isnull = True)
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without a release date',
		'productions': productions,
	})

def prods_without_release_date_with_placement(request):
	productions = Production.objects.raw('''
		SELECT DISTINCT ON (demoscene_production.id)
			demoscene_production.*,
			demoscene_party.end_date_date AS suggested_release_date_date,
			demoscene_party.end_date_precision AS suggested_release_date_precision,
			demoscene_party.name AS release_detail
		FROM
			demoscene_production
			INNER JOIN demoscene_competitionplacing ON (demoscene_production.id = demoscene_competitionplacing.production_id)
			INNER JOIN demoscene_competition ON (demoscene_competitionplacing.competition_id = demoscene_competition.id  AND demoscene_competition.name <> 'Invitation')
			INNER JOIN demoscene_party ON (demoscene_competition.party_id = demoscene_party.id)
		WHERE
			demoscene_production.release_date_date IS NULL
		ORDER BY demoscene_production.id, demoscene_party.end_date_date
	''')
	
	productions = list(productions)
	for production in productions:
		production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Productions without a release date but with a party placement attached',
		'productions': productions,
		'return_to': reverse('maintenance_prods_without_release_date_with_placement'),
	})

def prod_soundtracks_without_release_date(request):
	productions = Production.objects.raw('''
		SELECT DISTINCT ON (soundtrack.id)
			soundtrack.*,
			production.release_date_date AS suggested_release_date_date,
			production.release_date_precision AS suggested_release_date_precision,
			production.title AS release_detail
		FROM
			demoscene_production AS soundtrack
			INNER JOIN demoscene_soundtracklink ON (soundtrack.id = demoscene_soundtracklink.soundtrack_id)
			INNER JOIN demoscene_production AS production ON (demoscene_soundtracklink.production_id = production.id)
		WHERE
			soundtrack.release_date_date IS NULL
		ORDER BY
			soundtrack.id, production.release_date_date
	''')
	productions = list(productions)
	for production in productions:
		if production.suggested_release_date_date != None:
			production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Music with productions attached but no release date',
		'productions': productions,
		'return_to': reverse('maintenance_prod_soundtracks_without_release_date'),
	})

def group_nicks_with_brackets(request):
	nicks = Nick.objects.filter(name__contains = '(', releaser__is_group = True).order_by('name')
	return render(request, 'maintenance/nick_report.html', {
		'title': 'Group names with brackets',
		'nicks': nicks,
	})

def ambiguous_groups_with_no_differentiators(request):
	nicks = Nick.objects.raw('''
		SELECT demoscene_nick.*
		FROM
			demoscene_nick
			INNER JOIN demoscene_releaser ON (demoscene_nick.releaser_id = demoscene_releaser.id)
			INNER JOIN demoscene_nick AS same_named_nick ON (
				demoscene_nick.name = same_named_nick.name
				AND demoscene_nick.releaser_id <> same_named_nick.releaser_id)
			INNER JOIN demoscene_releaser AS same_named_releaser ON (
				same_named_nick.releaser_id = same_named_releaser.id
				AND same_named_releaser.is_group = 't'
			)
		WHERE
			demoscene_releaser.is_group = 't'
			AND demoscene_nick.differentiator = ''
		ORDER BY demoscene_nick.name
	''')
	return render(request, 'maintenance/nick_report.html', {
		'title': 'Ambiguous group names with no differentiators',
		'nicks': nicks,
	})

def non_standard_credits(request):
	credits = Credit.objects.raw(r'''
		SELECT demoscene_credit.id, demoscene_credit.production_id, demoscene_production.title, demoscene_nick.name, role
		FROM demoscene_credit
		INNER JOIN demoscene_production ON (demoscene_credit.production_id = demoscene_production.id)
		INNER JOIN demoscene_nick ON (demoscene_credit.nick_id = demoscene_nick.id)
		WHERE role !~* '^(Code|Music|Graphics|Other)( \\([^\\)]+\\))?(, (Code|Music|Graphics|Other)( \\([^\\)]+\\))?)*$'
		ORDER BY role, title
	''')
	return render(request, 'maintenance/non_standard_credits.html', {
		'credits': credits,
	})

def replace_credit_role(request):
	if not request.user.is_staff:
		return redirect('home')
	old_role = request.POST['old_role']
	new_role = request.POST['new_role']
	cursor = connection.cursor()
	cursor.execute("UPDATE demoscene_credit SET role = %s WHERE role = %s", [new_role, old_role])
	transaction.commit_unless_managed()
	return redirect('maintenance_non_standard_credits')

def prods_with_release_date_outside_party(request):
	productions = Production.objects.raw('''
		SELECT * FROM (
			SELECT DISTINCT ON (demoscene_production.id)
				demoscene_production.*,
				demoscene_party.start_date_date AS party_start_date,
				demoscene_party.end_date_date AS party_end_date,
				demoscene_party.end_date_date AS suggested_release_date_date,
				demoscene_party.end_date_precision AS suggested_release_date_precision,
				demoscene_party.name AS release_detail,
				demoscene_party.end_date_precision AS party_end_date_precision
			FROM
				demoscene_production
				INNER JOIN demoscene_competitionplacing ON (demoscene_production.id = demoscene_competitionplacing.production_id)
				INNER JOIN demoscene_competition ON (demoscene_competitionplacing.competition_id = demoscene_competition.id  AND demoscene_competition.name <> 'Invitation')
				INNER JOIN demoscene_party ON (demoscene_competition.party_id = demoscene_party.id)
			WHERE
				demoscene_production.release_date_date IS NOT NULL
				AND demoscene_production.release_date_precision = 'd'
			ORDER BY demoscene_production.id, demoscene_party.end_date_date
		) AS releases
		WHERE
			releases.party_end_date_precision = 'd'
			AND (
				releases.release_date_date < releases.party_start_date - INTERVAL '14 days'
				OR releases.release_date_date > releases.party_end_date + INTERVAL '14 days'
			)
	''')
	productions = list(productions)
	for production in productions:
		production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Productions with a release date more than 14 days away from their release party',
		'productions': productions,
		'return_to': reverse('maintenance_prods_with_release_date_outside_party'),
	})

def fix_release_dates(request):
	if not request.user.is_staff:
		return redirect('home')
	for prod_id in request.POST.getlist('production_id'):
		prod = Production.objects.get(id = prod_id)
		prod.release_date_date = request.POST['production_%s_release_date_date' % prod_id]
		prod.release_date_precision = request.POST['production_%s_release_date_precision' % prod_id]
		prod.save()
	return HttpResponseRedirect(request.POST['return_to'])
	