from demoscene.shortcuts import *
from django.contrib.auth.decorators import login_required
from demoscene.models import Production, Nick, Credit, Releaser, Membership, ReleaserExternalLink, PartyExternalLink, Party
from sceneorg.models import Directory
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
	
	def releaser_duplicates_by_link_class(link_class):
		return Releaser.objects.raw('''
			SELECT DISTINCT demoscene_releaser.*, demoscene_releaserexternallink.parameter
			FROM demoscene_releaser
			INNER JOIN demoscene_releaserexternallink ON (
				demoscene_releaser.id = demoscene_releaserexternallink.releaser_id
				AND demoscene_releaserexternallink.link_class = %s)
			INNER JOIN demoscene_releaserexternallink AS other_link ON (
				demoscene_releaserexternallink.link_class = other_link.link_class
				AND demoscene_releaserexternallink.parameter = other_link.parameter
				AND demoscene_releaserexternallink.id <> other_link.id
			)
			ORDER BY demoscene_releaserexternallink.parameter
		''', [link_class])
	
	prod_dupes = {}
	for column in Production.external_site_ref_field_names:
		prod_dupes[column] = prod_duplicates_by_column(column)
	
	releaser_dupes = {}
	for link_class in ReleaserExternalLink.objects.distinct().values_list('link_class', flat=True):
		releaser_dupes[link_class] = releaser_duplicates_by_link_class(link_class)
	
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

def multiple_credits(request):
	report_name = 'multiple_credits'
	
	productions = Production.objects.raw('''
		SELECT DISTINCT demoscene_production.*, demoscene_nick.name AS nick_1, other_nick.name AS nick_2
		FROM
			demoscene_credit
			INNER JOIN demoscene_nick ON (demoscene_credit.nick_id = demoscene_nick.id)
			INNER JOIN demoscene_credit AS other_credit ON (
				demoscene_credit.production_id = other_credit.production_id
				AND demoscene_credit.id < other_credit.id
			)
			INNER JOIN demoscene_nick AS other_nick ON (
				other_credit.nick_id = other_nick.id
				AND demoscene_nick.releaser_id = other_nick.releaser_id
			)
			INNER JOIN demoscene_production ON (demoscene_credit.production_id = demoscene_production.id)
		ORDER BY demoscene_production.title
	''')
	return render(request, 'maintenance/multiple_credits_report.html', {
		'title': 'People with multiple credits on one production (including under different nicks)',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})
	
def implied_memberships(request):
	report_name = 'implied_memberships'
	
	cursor = connection.cursor()
	cursor.execute("""
		SELECT
			member.id, member.is_group, member.name,
			grp.id, grp.name,
			demoscene_production.id, demoscene_production.supertype, demoscene_production.title
		FROM
			demoscene_production
			INNER JOIN demoscene_production_author_nicks ON (demoscene_production.id = demoscene_production_author_nicks.production_id)
			INNER JOIN demoscene_nick AS author_nick ON (demoscene_production_author_nicks.nick_id = author_nick.id)
			INNER JOIN demoscene_releaser AS member ON (author_nick.releaser_id = member.id)
			INNER JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production.id = demoscene_production_author_affiliation_nicks.production_id)
			INNER JOIN demoscene_nick AS group_nick ON (demoscene_production_author_affiliation_nicks.nick_id = group_nick.id)
			INNER JOIN demoscene_releaser AS grp ON (group_nick.releaser_id = grp.id)
			LEFT JOIN demoscene_membership ON (
				member.id = demoscene_membership.member_id
				AND grp.id = demoscene_membership.group_id)
		WHERE
			demoscene_membership.id IS NULL
		ORDER BY
			grp.name, grp.id, member.name, member.id, demoscene_production.title
	""")
	records = [
		{
			'membership': (member_id, group_id),
			'member_id': member_id, 'member_is_group': member_is_group, 'member_name': member_name,
			'group_id': group_id, 'group_name': group_name,
			'production_id': production_id, 'production_supertype': production_supertype, 'production_title': production_title
		}
		for (member_id, member_is_group, member_name, group_id, group_name, production_id, production_supertype, production_title) in cursor.fetchall()
	]
	return render(request, 'maintenance/implied_memberships.html', {
		'title': 'Group memberships found in production bylines, but missing from the member list',
		'records': records,
		'report_name': report_name,
	})

def groups_with_same_named_members(request):
	report_name = 'groups_with_same_named_members'
	groups = Releaser.objects.raw('''
		SELECT grp.id, grp.name,
			demoscene_nickvariant.name AS member_1_name, scener.id AS member_1_id, scener.is_group AS member_1_is_group,
			other_nickvariant.name AS member_2_name, other_scener.id AS member_2_id, other_scener.is_group AS member_2_is_group
		FROM demoscene_nickvariant
		INNER JOIN demoscene_nick ON (demoscene_nickvariant.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_releaser AS scener ON (demoscene_nick.releaser_id = scener.id)
		INNER JOIN demoscene_membership ON (scener.id = demoscene_membership.member_id)
		INNER JOIN demoscene_releaser AS grp ON (demoscene_membership.group_id = grp.id)
		INNER JOIN demoscene_membership AS other_membership ON (
			other_membership.group_id = grp.id
			AND demoscene_membership.id < other_membership.id
		)
		INNER JOIN demoscene_releaser AS other_scener ON (other_membership.member_id = other_scener.id)
		INNER JOIN demoscene_nick AS other_nick ON (other_scener.id = other_nick.releaser_id)
		INNER JOIN demoscene_nickvariant AS other_nickvariant ON (
			other_nick.id = other_nickvariant.nick_id AND LOWER(demoscene_nickvariant.name) = LOWER (other_nickvariant.name)
		)
	''')
	return render(request, 'maintenance/groups_with_same_named_members.html', {
		'title': 'Groups with same-named members',
		'groups': groups,
		'report_name': report_name,
	})

def releasers_with_same_named_groups(request):
	report_name = 'releasers_with_same_named_groups'
	releasers = Releaser.objects.raw('''
		SELECT member.id, member.name, member.is_group,
			demoscene_nickvariant.name AS group_1_name, grp.id AS group_1_id,
			other_nickvariant.name AS group_2_name, other_grp.id AS group_2_id
		FROM demoscene_nickvariant
		INNER JOIN demoscene_nick ON (demoscene_nickvariant.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_releaser AS grp ON (demoscene_nick.releaser_id = grp.id)
		INNER JOIN demoscene_membership ON (grp.id = demoscene_membership.group_id)
		INNER JOIN demoscene_releaser AS member ON (demoscene_membership.member_id = member.id)
		INNER JOIN demoscene_membership AS other_membership ON (
			other_membership.member_id = member.id
			AND demoscene_membership.id < other_membership.id
		)
		INNER JOIN demoscene_releaser AS other_grp ON (other_membership.group_id = other_grp.id)
		INNER JOIN demoscene_nick AS other_nick ON (other_grp.id = other_nick.releaser_id)
		INNER JOIN demoscene_nickvariant AS other_nickvariant ON (
			other_nick.id = other_nickvariant.nick_id AND LOWER(demoscene_nickvariant.name) = LOWER (other_nickvariant.name)
		)
	''')
	return render(request, 'maintenance/releasers_with_same_named_groups.html', {
		'title': 'Releasers with same-named groups',
		'releasers': releasers,
		'report_name': report_name,
	})

def sceneorg_party_dirs_with_no_party(request):
	report_name = 'sceneorg_party_dirs_with_no_party'
	
	directories_plain = Directory.objects.raw('''
		SELECT party_dir.*
		FROM sceneorg_directory AS parties_root
		INNER JOIN sceneorg_directory AS party_years ON (parties_root.id = party_years.parent_id)
		INNER JOIN sceneorg_directory AS party_dir ON (party_years.id = party_dir.parent_id)
		LEFT JOIN demoscene_partyexternallink ON (link_class = 'SceneOrgFolder' AND parameter = party_dir.path)
		WHERE parties_root.path = '/parties/'
		AND demoscene_partyexternallink.id IS NULL
		ORDER BY party_dir.path
	''')
	
	directories = Directory.objects.raw('''
		SELECT party_dir.*,
			demoscene_partyseries.name AS suggested_series_name,
			demoscene_partyseries.id AS suggested_series_id,
			demoscene_party.name AS suggested_party_name,
			demoscene_party.id AS suggested_party_id,
			substring(party_dir.path from '/parties/(\\\\d+)/') AS party_year
		FROM sceneorg_directory AS parties_root
		INNER JOIN sceneorg_directory AS party_years ON (parties_root.id = party_years.parent_id)
		INNER JOIN sceneorg_directory AS party_dir ON (party_years.id = party_dir.parent_id)
		LEFT JOIN demoscene_partyexternallink ON (link_class = 'SceneOrgFolder' AND parameter = party_dir.path)
		LEFT JOIN demoscene_partyseries ON (
			regexp_replace(substring(lower(party_dir.path) from '/parties/\\\\d+/([-a-z_]+)'), '[^a-z]', '', 'g')
			= regexp_replace(lower(demoscene_partyseries.name), '[^a-z]', '', 'g')
		)
		LEFT JOIN demoscene_party ON (
			demoscene_partyseries.id = demoscene_party.party_series_id
			AND substring(party_dir.path from '/parties/(\\\\d+)/')
				= cast(extract(year from demoscene_party.start_date_date) as varchar)
		)
		WHERE parties_root.path = '/parties/'
		AND demoscene_partyexternallink.id IS NULL
		ORDER BY party_dir.path
	''')
	total_count = Directory.parties().count()
	unmatched_count = len(list(directories_plain))
	matched_count = total_count - unmatched_count
	
	return render(request, 'maintenance/sceneorg_party_dirs_with_no_party.html', {
		'title': 'scene.org party dirs which are not linked to a party',
		'directories': directories,
		'report_name': report_name,
		'total_count': total_count,
		'matched_count': matched_count,
	})

def parties_with_incomplete_dates(request):
	report_name = 'parties_with_incomplete_dates'
	parties = Party.objects.extra(
		where = [
			"(start_date_precision <> 'd' OR end_date_precision <> 'd')",
			"demoscene_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
		],
		params = [report_name]
	).order_by('start_date_date')
	
	return render(request, 'maintenance/party_report.html', {
		'title': 'Parties with incomplete dates',
		'parties': parties,
		'report_name': report_name,
	})

def parties_with_no_location(request):
	report_name = 'parties_with_no_location'
	parties = Party.objects.extra(
		where = [
			"woe_id IS NULL",
			"demoscene_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
		],
		params = [report_name]
	).order_by('start_date_date')
	
	return render(request, 'maintenance/party_report.html', {
		'title': 'Parties with no location',
		'parties': parties,
		'report_name': report_name,
	})

def empty_releasers(request):
	report_name = 'empty_releasers'
	releasers = Releaser.objects.raw('''
		SELECT
			demoscene_releaser.*
		FROM demoscene_releaser
		LEFT JOIN demoscene_membership AS groups ON groups.member_id = demoscene_releaser.id
		LEFT JOIN demoscene_membership AS members ON members.group_id = demoscene_releaser.id
		WHERE
		demoscene_releaser.notes = ''
		AND groups.group_id IS NULL
		AND members.member_id IS NULL
		AND (
			SELECT COUNT (demoscene_nick.id)
			FROM demoscene_nick
			LEFT JOIN demoscene_production_author_nicks ON (demoscene_nick.id = demoscene_production_author_nicks.nick_id)
			LEFT JOIN demoscene_production_author_affiliation_nicks ON (demoscene_nick.id = demoscene_production_author_affiliation_nicks.nick_id)
			LEFT JOIN demoscene_credit ON (demoscene_nick.id = demoscene_credit.nick_id)
			WHERE demoscene_nick.releaser_id = demoscene_releaser.id
			AND (demoscene_production_author_nicks.nick_id IS NOT NULL
			OR demoscene_production_author_affiliation_nicks.nick_id IS NOT NULL
			OR demoscene_credit.nick_id IS NOT NULL)
		) = 0
		AND demoscene_releaser.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY demoscene_releaser.name
	''', [report_name])
	
	return render(request, 'maintenance/releaser_report.html', {
		'title': 'Empty releaser records',
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

def add_membership(request):
	if not request.user.is_staff:
		return redirect('home')
	try:
		Membership.objects.get(
			member__id = request.POST['member_id'],
			group__id = request.POST['group_id']
		)
	except Membership.DoesNotExist:
		Membership.objects.create(
			member_id = request.POST['member_id'],
			group_id = request.POST['group_id']
		)
	return HttpResponse('OK', mimetype='text/plain')

def add_sceneorg_link_to_party(request):
	if not request.user.is_staff:
		return redirect('home')
	if request.POST and request.POST.get('path') and request.POST.get('party_id'):
		PartyExternalLink.objects.create(
			party_id = request.POST['party_id'],
			parameter = request.POST['path'],
			link_class = 'SceneOrgFolder')
	return HttpResponse('OK', mimetype='text/plain')
