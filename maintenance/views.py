from demoscene.shortcuts import *
from django.contrib.auth.decorators import login_required
from demoscene.models import Production, Nick, Credit, Releaser
from maintenance.models import Exclusion
from django.db import connection, transaction
from fuzzy_date import FuzzyDate
from django.http import HttpResponse, HttpResponseRedirect

def index(request):
	if not request.user.is_staff:
		return redirect('home')
	return render(request, 'maintenance/index.html')

def prods_without_screenshots(request):
	report_name = 'prods_without_screenshots'
	
	productions = Production.objects \
		.filter(screenshots__id__isnull = True) \
		.exclude(supertype = 'music') \
		.extra(
			where = ['demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params = [report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without screenshots',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})

def prods_without_external_links(request):
	report_name = 'prods_without_external_links'
	
	filters = {}
	for field in Production.external_site_ref_field_names:
		filters["%s__isnull" % field] = True
	
	productions = Production.objects \
		.filter(supertype = 'production', **filters) \
		.extra(
			where = ['demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params = [report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without external links',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})

def prods_without_release_date(request):
	report_name = 'prods_without_release_date'
	
	productions = Production.objects.filter(release_date_date__isnull = True) \
		.extra(
			where = ['demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params = [report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without a release date',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})

def prods_without_release_date_with_placement(request):
	report_name = 'prods_without_release_date_with_placement'
	
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
			AND demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY demoscene_production.id, demoscene_party.end_date_date
	''', [report_name])
	
	productions = list(productions)
	for production in productions:
		production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Productions without a release date but with a party placement attached',
		'productions': productions,
		'report_name': report_name,
		'return_to': reverse('maintenance_prods_without_release_date_with_placement'),
	})

def prod_soundtracks_without_release_date(request):
	report_name = 'prod_soundtracks_without_release_date'
	
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
			AND soundtrack.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY
			soundtrack.id, production.release_date_date
	''', [report_name])
	productions = list(productions)
	for production in productions:
		if production.suggested_release_date_date != None:
			production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Music with productions attached but no release date',
		'productions': productions,
		'report_name': report_name,
		'return_to': reverse('maintenance_prod_soundtracks_without_release_date'),
	})

def group_nicks_with_brackets(request):
	report_name = 'group_nicks_with_brackets'
	
	nicks = Nick.objects.filter(name__contains = '(', releaser__is_group = True) \
		.extra(
			where = ['demoscene_nick.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params = [report_name]
		).order_by('name')
	return render(request, 'maintenance/nick_report.html', {
		'title': 'Group names with brackets',
		'nicks': nicks,
		'report_name': report_name,
	})

def ambiguous_groups_with_no_differentiators(request):
	report_name = 'ambiguous_groups_with_no_differentiators'
	
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
			AND demoscene_nick.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY demoscene_nick.name
	''', [report_name])
	return render(request, 'maintenance/nick_report.html', {
		'title': 'Ambiguous group names with no differentiators',
		'nicks': nicks,
		'report_name': report_name,
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
	report_name = 'prods_with_release_date_outside_party'
	
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
			AND releases.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
	''', [report_name])
	productions = list(productions)
	for production in productions:
		production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
	
	return render(request, 'maintenance/production_release_date_report.html', {
		'title': 'Productions with a release date more than 14 days away from their release party',
		'productions': productions,
		'report_name': report_name,
		'return_to': reverse('maintenance_prods_with_release_date_outside_party'),
	})

def prods_with_same_named_credits(request):
	report_name = 'prods_with_same_named_credits'
	
	productions = Production.objects.raw('''
		SELECT DISTINCT demoscene_production.*
		FROM demoscene_production
		INNER JOIN demoscene_credit ON (demoscene_production.id = demoscene_credit.production_id)
		INNER JOIN demoscene_nick ON (demoscene_credit.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.name = other_nick.name AND demoscene_nick.id <> other_nick.id)
		INNER JOIN demoscene_credit AS other_credit ON (other_nick.id = other_credit.nick_id AND other_credit.production_id = demoscene_production.id)
		AND demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
	''', [report_name])
	
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions with identically-named sceners in the credits',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})

def same_named_prods_by_same_releaser(request):
	report_name = 'same_named_prods_by_same_releaser'
	
	productions = Production.objects.raw('''
		SELECT DISTINCT demoscene_production.*, LOWER(demoscene_production.title) AS lower_title
		FROM demoscene_production
		INNER JOIN demoscene_production_author_nicks ON (demoscene_production.id = demoscene_production_author_nicks.production_id)
		INNER JOIN demoscene_nick ON (demoscene_production_author_nicks.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.releaser_id = other_nick.releaser_id)
		INNER JOIN demoscene_production_author_nicks AS other_authorship ON (other_nick.id = other_authorship.nick_id)
		INNER JOIN demoscene_production AS other_production ON (other_authorship.production_id = other_production.id)
		WHERE
			demoscene_production.title <> '?'
			AND demoscene_production.id <> other_production.id AND LOWER(demoscene_production.title) = LOWER(other_production.title)
			AND demoscene_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY lower_title
	''', [report_name])
	
	return render(request, 'maintenance/production_report.html', {
		'title': 'Identically-named productions by the same releaser',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})

def duplicate_external_links(request):
	def prod_duplicates_by_column(column_name):
		return Production.objects.raw('''
			SELECT DISTINCT demoscene_production.*
			FROM demoscene_production
			INNER JOIN demoscene_production AS other_production ON (
				demoscene_production.%s IS NOT NULL
				AND demoscene_production.%s = other_production.%s
				AND demoscene_production.id <> other_production.id)
			ORDER BY demoscene_production.%s
		''' % ((column_name,)*4) )
	
	def releaser_duplicates_by_column(column_name):
		return Releaser.objects.raw('''
			SELECT DISTINCT demoscene_releaser.*
			FROM demoscene_releaser
			INNER JOIN demoscene_releaser AS other_releaser ON (
				demoscene_releaser.%s IS NOT NULL
				AND demoscene_releaser.%s = other_releaser.%s
				AND demoscene_releaser.id <> other_releaser.id)
			ORDER BY demoscene_releaser.%s
		''' % ((column_name,)*4) )
	
	prod_dupes = {}
	for column in Production.external_site_ref_field_names:
		prod_dupes[column] = prod_duplicates_by_column(column)
	
	releaser_dupes = {}
	for column in Releaser.external_site_ref_field_names:
		if column == 'asciiarena_author_id':
			continue
		releaser_dupes[column] = releaser_duplicates_by_column(column)
	# specialcase asciiarena_author_id - blank entries are '', not null
	releaser_dupes['asciiarena_author_id'] = Releaser.objects.raw('''
		SELECT DISTINCT demoscene_releaser.*
		FROM demoscene_releaser
		INNER JOIN demoscene_releaser AS other_releaser ON (
			demoscene_releaser.asciiarena_author_id <> ''
			AND demoscene_releaser.asciiarena_author_id = other_releaser.asciiarena_author_id
			AND demoscene_releaser.id <> other_releaser.id)
		ORDER BY demoscene_releaser.asciiarena_author_id
	''')
	
	return render(request, 'maintenance/duplicate_external_links.html', {
		'prod_dupes': prod_dupes,
		'releaser_dupes': releaser_dupes,
	})

def matching_real_names(request):
	report_name = 'matching_real_names'
	
	releasers = Releaser.objects.raw('''
		SELECT DISTINCT demoscene_releaser.*
		FROM demoscene_releaser
		INNER JOIN demoscene_releaser AS other_releaser ON (
			demoscene_releaser.first_name <> ''
			AND demoscene_releaser.surname <> ''
			AND demoscene_releaser.first_name = other_releaser.first_name
			AND demoscene_releaser.surname = other_releaser.surname
			AND demoscene_releaser.id <> other_releaser.id)
		ORDER BY demoscene_releaser.first_name, demoscene_releaser.surname, demoscene_releaser.name
	''')
	return render(request, 'maintenance/matching_real_names.html', {
		'title': 'Sceners with matching real names',
		'releasers': releasers,
		'report_name': report_name,
	})

def matching_surnames(request):
	report_name = 'matching_surnames'
	
	releasers = Releaser.objects.raw('''
		SELECT DISTINCT demoscene_releaser.*
		FROM demoscene_releaser
		INNER JOIN demoscene_releaser AS other_releaser ON (
			demoscene_releaser.surname <> ''
			AND demoscene_releaser.surname = other_releaser.surname
			AND demoscene_releaser.id <> other_releaser.id)
		ORDER BY demoscene_releaser.surname, demoscene_releaser.first_name, demoscene_releaser.name
	''')
	return render(request, 'maintenance/matching_surnames.html', {
		'title': 'Sceners with matching surnames',
		'releasers': releasers,
		'report_name': report_name,
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

def exclude(request):
	if not request.user.is_staff:
		return redirect('home')
	Exclusion.objects.create(
		report_name = request.POST['report_name'],
		record_id = request.POST['record_id']
	)
	return HttpResponse('OK', mimetype='text/plain')
