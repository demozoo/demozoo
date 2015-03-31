from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, get_object_or_404

from fuzzy_date import FuzzyDate
from read_only_mode import writeable_site_required

from demoscene.models import Nick, Releaser, Membership, ReleaserExternalLink
from comments.models import Comment
from parties.models import PartyExternalLink, Party, ResultsFile
from productions.models import Production, Credit, ProductionLink, ProductionBlurb
from sceneorg.models import Directory
from maintenance.models import Exclusion
from mirror.models import Download, ArchiveMember
from screenshots.tasks import create_screenshot_from_production_link



def index(request):
	if not request.user.is_staff:
		return redirect('home')
	return render(request, 'maintenance/index.html')


def prods_without_screenshots(request):
	report_name = 'prods_without_screenshots'

	productions = Production.objects \
		.filter(screenshots__id__isnull=True) \
		.exclude(supertype='music') \
		.extra(
			where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without screenshots',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_without_external_links(request):
	report_name = 'prods_without_external_links'

	productions = Production.objects.raw('''
		SELECT productions_production.*
		FROM productions_production
		LEFT JOIN productions_productionlink ON (
			productions_production.id = productions_productionlink.production_id
			AND productions_productionlink.is_download_link = 'f'
		)
		WHERE productions_production.supertype = 'production'
		AND productions_productionlink.id IS NULL
		AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY productions_production.title
	''', [report_name])
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without external links',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_without_release_date(request):
	report_name = 'prods_without_release_date'

	productions = Production.objects.filter(release_date_date__isnull=True) \
		.extra(
			where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without a release date',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_with_dead_amigascne_links(request):
	report_name = 'prods_with_dead_amigascne_links'

	productions = Production.objects.filter(links__parameter__contains='amigascne.org/old/') \
		.extra(
			where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions with dead amigascne links',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_with_dead_amiga_nvg_org_links(request):
	report_name = 'prods_with_dead_amiga_nvg_org_links'

	productions = Production.objects.filter(links__parameter__contains='amiga.nvg.org') \
		.extra(
			where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[report_name]
		).order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions with dead amiga.nvg.org links',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_without_platforms(request):
	report_name = 'prods_without_platforms'

	productions = Production.objects.filter(platforms__isnull=True, supertype='production') \
		.exclude(types__name='Video') \
		.extra(
			where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[report_name]
		).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('title')
	return render(request, 'maintenance/production_report.html', {
		'title': 'Productions without platforms',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def prods_without_release_date_with_placement(request):
	report_name = 'prods_without_release_date_with_placement'

	productions = Production.objects.raw('''
		SELECT DISTINCT ON (productions_production.id)
			productions_production.*,
			parties_party.end_date_date AS suggested_release_date_date,
			parties_party.end_date_precision AS suggested_release_date_precision,
			parties_party.name AS release_detail
		FROM
			productions_production
			INNER JOIN parties_competitionplacing ON (productions_production.id = parties_competitionplacing.production_id)
			INNER JOIN parties_competition ON (parties_competitionplacing.competition_id = parties_competition.id  AND parties_competition.name <> 'Invitation')
			INNER JOIN parties_party ON (parties_competition.party_id = parties_party.id)
		WHERE
			productions_production.release_date_date IS NULL
			AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY productions_production.id, parties_party.end_date_date
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
			productions_production AS soundtrack
			INNER JOIN productions_soundtracklink ON (soundtrack.id = productions_soundtracklink.soundtrack_id)
			INNER JOIN productions_production AS production ON (productions_soundtracklink.production_id = production.id)
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

	nicks = Nick.objects.filter(name__contains = '(', releaser__is_group=True) \
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
		SELECT demoscene_nick.*,
			same_named_releaser.id AS clashing_id, same_named_nick.name AS clashing_name, same_named_nick.differentiator AS clashing_differentiator
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
	return render(request, 'maintenance/ambiguous_group_names.html', {
		'title': 'Ambiguous group names with no differentiators',
		'nicks': nicks,
		'report_name': report_name,
	})


def prods_with_release_date_outside_party(request):
	report_name = 'prods_with_release_date_outside_party'

	productions = Production.objects.raw('''
		SELECT * FROM (
			SELECT DISTINCT ON (productions_production.id)
				productions_production.*,
				parties_party.start_date_date AS party_start_date,
				parties_party.end_date_date AS party_end_date,
				parties_party.end_date_date AS suggested_release_date_date,
				parties_party.end_date_precision AS suggested_release_date_precision,
				parties_party.name AS release_detail,
				parties_party.end_date_precision AS party_end_date_precision
			FROM
				productions_production
				INNER JOIN parties_competitionplacing ON (productions_production.id = parties_competitionplacing.production_id)
				INNER JOIN parties_competition ON (parties_competitionplacing.competition_id = parties_competition.id  AND parties_competition.name <> 'Invitation')
				INNER JOIN parties_party ON (parties_competition.party_id = parties_party.id)
			WHERE
				productions_production.release_date_date IS NOT NULL
				AND productions_production.release_date_precision = 'd'
			ORDER BY productions_production.id, parties_party.end_date_date
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
		SELECT DISTINCT productions_production.*
		FROM productions_production
		INNER JOIN productions_credit ON (productions_production.id = productions_credit.production_id)
		INNER JOIN demoscene_nick ON (productions_credit.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.name = other_nick.name AND demoscene_nick.id <> other_nick.id)
		INNER JOIN productions_credit AS other_credit ON (other_nick.id = other_credit.nick_id AND other_credit.production_id = productions_production.id)
		AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
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
		SELECT DISTINCT productions_production.*
		FROM productions_production
		INNER JOIN productions_production_author_nicks ON (productions_production.id = productions_production_author_nicks.production_id)
		INNER JOIN demoscene_nick ON (productions_production_author_nicks.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.releaser_id = other_nick.releaser_id)
		INNER JOIN productions_production_author_nicks AS other_authorship ON (other_nick.id = other_authorship.nick_id)
		INNER JOIN productions_production AS other_production ON (other_authorship.production_id = other_production.id)
		WHERE
			productions_production.title <> '?'
			AND productions_production.id <> other_production.id AND LOWER(productions_production.title) = LOWER(other_production.title)
			AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name IN ('same_named_prods_by_same_releaser', 'same_named_prods_without_special_chars') )
		ORDER BY productions_production.sortable_title
	''', [report_name])

	return render(request, 'maintenance/production_report.html', {
		'title': 'Identically-named productions by the same releaser',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def same_named_prods_without_special_chars(request):
	report_name = 'same_named_prods_without_special_chars'

	productions = Production.objects.raw('''
		SELECT DISTINCT productions_production.*
		FROM productions_production
		INNER JOIN productions_production_author_nicks ON (productions_production.id = productions_production_author_nicks.production_id)
		INNER JOIN demoscene_nick ON (productions_production_author_nicks.nick_id = demoscene_nick.id)
		INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.releaser_id = other_nick.releaser_id)
		INNER JOIN productions_production_author_nicks AS other_authorship ON (other_nick.id = other_authorship.nick_id)
		INNER JOIN productions_production AS other_production ON (other_authorship.production_id = other_production.id)
		WHERE
			productions_production.title <> '?'
			AND productions_production.id <> other_production.id
			AND LOWER(REGEXP_REPLACE(productions_production.title, E'\\\\W', '', 'g')) = LOWER(REGEXP_REPLACE(other_production.title, E'\\\\W', '', 'g'))
			AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name IN ('same_named_prods_by_same_releaser', 'same_named_prods_without_special_chars') )
		ORDER BY productions_production.sortable_title
	''')

	return render(request, 'maintenance/production_report.html', {
		'title': 'Identically-named productions by the same releaser, ignoring special chars',
		'productions': productions,
		'mark_excludable': True,
		'report_name': report_name,
	})


def duplicate_external_links(request):
	def prod_duplicates_by_link_class(link_class):
		return Production.objects.raw('''
			SELECT DISTINCT productions_production.*, productions_productionlink.parameter
			FROM productions_production
			INNER JOIN productions_productionlink ON (
				productions_production.id = productions_productionlink.production_id
				AND productions_productionlink.link_class = %s
				AND productions_productionlink.is_download_link = 'f')
			INNER JOIN productions_productionlink AS other_link ON (
				productions_productionlink.link_class = other_link.link_class
				AND productions_productionlink.parameter = other_link.parameter
				AND productions_productionlink.id <> other_link.id
				AND productions_productionlink.is_download_link = 'f'
			)
			ORDER BY productions_productionlink.parameter
		''', [link_class])

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
	for link_class in ProductionLink.objects.distinct().values_list('link_class', flat=True):
		prod_dupes[link_class] = prod_duplicates_by_link_class(link_class)

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


def implied_memberships(request):
	report_name = 'implied_memberships'

	cursor = connection.cursor()
	cursor.execute("""
		SELECT
			member.id, member.is_group, member.name,
			grp.id, grp.name,
			productions_production.id, productions_production.supertype, productions_production.title
		FROM
			productions_production
			INNER JOIN productions_production_author_nicks ON (productions_production.id = productions_production_author_nicks.production_id)
			INNER JOIN demoscene_nick AS author_nick ON (productions_production_author_nicks.nick_id = author_nick.id)
			INNER JOIN demoscene_releaser AS member ON (author_nick.releaser_id = member.id)
			INNER JOIN productions_production_author_affiliation_nicks ON (productions_production.id = productions_production_author_affiliation_nicks.production_id)
			INNER JOIN demoscene_nick AS group_nick ON (productions_production_author_affiliation_nicks.nick_id = group_nick.id)
			INNER JOIN demoscene_releaser AS grp ON (group_nick.releaser_id = grp.id)
			LEFT JOIN demoscene_membership ON (
				member.id = demoscene_membership.member_id
				AND grp.id = demoscene_membership.group_id)
		WHERE
			demoscene_membership.id IS NULL
		ORDER BY
			grp.name, grp.id, member.name, member.id, productions_production.title
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
		LEFT JOIN parties_partyexternallink ON (link_class = 'SceneOrgFolder' AND parameter = party_dir.path)
		WHERE parties_root.path = '/parties/'
		AND parties_partyexternallink.id IS NULL
		AND party_dir.is_deleted = 'f'
		ORDER BY party_dir.path
	''')

	directories = Directory.objects.raw('''
		SELECT party_dir.*,
			parties_partyseries.name AS suggested_series_name,
			parties_partyseries.id AS suggested_series_id,
			parties_party.name AS suggested_party_name,
			parties_party.id AS suggested_party_id,
			substring(party_dir.path from '/parties/(\\\\d+)/') AS party_year
		FROM sceneorg_directory AS parties_root
		INNER JOIN sceneorg_directory AS party_years ON (parties_root.id = party_years.parent_id)
		INNER JOIN sceneorg_directory AS party_dir ON (party_years.id = party_dir.parent_id)
		LEFT JOIN parties_partyexternallink ON (link_class = 'SceneOrgFolder' AND parameter = party_dir.path)
		LEFT JOIN parties_partyseries ON (
			regexp_replace(substring(lower(party_dir.path) from '/parties/\\\\d+/([-a-z_]+)'), '[^a-z]', '', 'g')
			= regexp_replace(lower(parties_partyseries.name), '[^a-z]', '', 'g')
		)
		LEFT JOIN parties_party ON (
			parties_partyseries.id = parties_party.party_series_id
			AND substring(party_dir.path from '/parties/(\\\\d+)/')
				= cast(extract(year from parties_party.start_date_date) as varchar)
		)
		WHERE parties_root.path = '/parties/'
		AND parties_partyexternallink.id IS NULL
		AND party_dir.is_deleted = 'f'
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
		where=[
			"(start_date_precision <> 'd' OR end_date_precision <> 'd')",
			"parties_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
		],
		params=[report_name]
	).order_by('start_date_date')

	return render(request, 'maintenance/party_report.html', {
		'title': 'Parties with incomplete dates',
		'parties': parties,
		'report_name': report_name,
	})


def parties_with_no_location(request):
	report_name = 'parties_with_no_location'
	parties = Party.objects.extra(
		where=[
			"latitude IS NULL",
			"is_online = 'f'",
			"parties_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
		],
		params=[report_name]
	).order_by('start_date_date')

	return render(request, 'maintenance/party_report.html', {
		'title': 'Parties with no location',
		'parties': parties,
		'report_name': report_name,
	})


def empty_releasers(request):
	report_name = 'empty_releasers'
	releasers = Releaser.objects.raw('''
		SELECT id, is_group, name
		FROM demoscene_releaser
		WHERE
		notes = ''
		AND id IN ( -- must belong to no groups
			SELECT demoscene_releaser.id
			FROM demoscene_releaser
			LEFT JOIN demoscene_membership AS groups ON groups.member_id = demoscene_releaser.id
			GROUP BY demoscene_releaser.id
			HAVING COUNT(group_id) = 0
		)
		AND id IN ( -- must have no members
			SELECT demoscene_releaser.id
			FROM demoscene_releaser
			LEFT JOIN demoscene_membership AS members ON members.group_id = demoscene_releaser.id
			GROUP BY demoscene_releaser.id
			HAVING COUNT(member_id) = 0
		)
		AND id IN ( -- must have no releases as author
			SELECT demoscene_releaser.id
			FROM demoscene_releaser
			LEFT JOIN demoscene_nick ON (demoscene_releaser.id = demoscene_nick.releaser_id)
			LEFT JOIN productions_production_author_nicks ON (demoscene_nick.id = productions_production_author_nicks.nick_id)
			GROUP BY demoscene_releaser.id
			HAVING COUNT(production_id) = 0
		)
		AND id IN ( -- must have no releases as author affiliation
			SELECT demoscene_releaser.id
			FROM demoscene_releaser
			LEFT JOIN demoscene_nick ON (demoscene_releaser.id = demoscene_nick.releaser_id)
			LEFT JOIN productions_production_author_affiliation_nicks ON (demoscene_nick.id = productions_production_author_affiliation_nicks.nick_id)
			GROUP BY demoscene_releaser.id
			HAVING COUNT(production_id) = 0
		)
		AND id IN ( -- must have no credits
			SELECT demoscene_releaser.id
			FROM demoscene_releaser
			LEFT JOIN demoscene_nick ON (demoscene_releaser.id = demoscene_nick.releaser_id)
			LEFT JOIN productions_credit ON (demoscene_nick.id = productions_credit.nick_id)
			GROUP BY demoscene_releaser.id
			HAVING COUNT(production_id) = 0
		)
		AND id NOT IN (SELECT releaser_id FROM demoscene_nick where differentiator <> '')
		AND id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		ORDER BY LOWER(name)
	''', [report_name])

	return render(request, 'maintenance/releaser_report.html', {
		'title': 'Empty releaser records',
		'releasers': releasers,
		'report_name': report_name,
	})


def unresolved_screenshots(request):
	links = ProductionLink.objects.filter(is_unresolved_for_screenshotting=True).select_related('production')

	entries = []
	for link in links[:100]:
		download = Download.last_mirrored_download_for_url(link.download_url)
		if download:
			entries.append((link, download, download.archive_members.all()))

	return render(request, 'maintenance/unresolved_screenshots.html', {
		'title': 'Unresolved screenshots',
		'link_count': links.count(),
		'entries': entries,
		'report_name': 'unresolved_screenshots',
	})


def public_real_names(request):
	if not request.user.is_staff:
		return redirect('home')

	has_public_first_name = (~Q(first_name='')) & Q(show_first_name=True)
	has_public_surname = (~Q(surname='')) & Q(show_surname=True)

	sceners = Releaser.objects.filter(
		Q(is_group=False),
		has_public_first_name | has_public_surname
	).order_by('name')

	if request.GET.get('without_note'):
		sceners = sceners.filter(real_name_note='')

	return render(request, 'maintenance/public_real_names.html', {
		'title': 'Sceners with public real names',
		'sceners': sceners,
		'report_name': 'public_real_names',
	})

def prods_with_blurbs(request):
	if not request.user.is_staff:
		return redirect('home')

	blurbs = ProductionBlurb.objects.select_related('production')

	return render(request, 'maintenance/prods_with_blurbs.html', {
		'blurbs': blurbs,
	})

def prod_comments(request):
	if not request.user.is_staff:
		return redirect('home')

	production_type = ContentType.objects.get_for_model(Production)

	comments = Comment.objects.filter(content_type=production_type).order_by('-created_at').select_related('user')
	paginator = Paginator(comments, 100)

	page = request.GET.get('page', 1)
	try:
		comments_page = paginator.page(page)
	except (PageNotAnInteger, EmptyPage):
		# If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
		comments_page = paginator.page(paginator.num_pages)

	return render(request, 'maintenance/prod_comments.html', {
		'comments': comments_page,
	})

def credits_to_move_to_text(request):
	if not request.user.is_staff:
		return redirect('home')

	report_name = 'credits_to_move_to_text'

	credits = Credit.objects.raw('''
		SELECT
			productions_credit.*,
			productions_production.title,
			demoscene_nick.name AS nick_name
		FROM productions_credit
		INNER JOIN productions_production ON productions_credit.production_id = productions_production.id
		INNER JOIN demoscene_nick ON productions_credit.nick_id = demoscene_nick.id
		WHERE category = 'Other'
		AND (
			production_id IN (SELECT production_id FROM productions_production_types where productiontype_id = 5)
			OR role ILIKE '%%text%%'
			OR role ILIKE '%%lyric%%'
		)
		AND productions_credit.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
	''', [report_name])

	return render(request, 'maintenance/credits_to_move_to_text.html', {
		'title': 'Credits that probably need to be moved to the Text category',
		'credits': credits,
		'mark_excludable': True,
		'report_name': report_name,
	})


@writeable_site_required
def fix_release_dates(request):
	if not request.user.is_staff:
		return redirect('home')
	for prod_id in request.POST.getlist('production_id'):
		prod = Production.objects.get(id=prod_id)
		prod.release_date_date = request.POST['production_%s_release_date_date' % prod_id]
		prod.release_date_precision = request.POST['production_%s_release_date_precision' % prod_id]
		prod.save()
	return HttpResponseRedirect(request.POST['return_to'])


@writeable_site_required
def exclude(request):
	if not request.user.is_staff:
		return redirect('home')
	Exclusion.objects.create(
		report_name=request.POST['report_name'],
		record_id=request.POST['record_id']
	)
	return HttpResponse('OK', mimetype='text/plain')


@writeable_site_required
def add_membership(request):
	if not request.user.is_staff:
		return redirect('home')
	try:
		Membership.objects.get(
			member__id=request.POST['member_id'],
			group__id=request.POST['group_id']
		)
	except Membership.DoesNotExist:
		Membership.objects.create(
			member_id=request.POST['member_id'],
			group_id=request.POST['group_id']
		)
	return HttpResponse('OK', mimetype='text/plain')


@writeable_site_required
def add_sceneorg_link_to_party(request):
	if not request.user.is_staff:
		return redirect('home')
	if request.POST and request.POST.get('path') and request.POST.get('party_id'):
		PartyExternalLink.objects.create(
			party_id=request.POST['party_id'],
			parameter=request.POST['path'],
			link_class='SceneOrgFolder')
	return HttpResponse('OK', mimetype='text/plain')


def view_archive_member(request, archive_member_id):
	if not request.user.is_staff:
		return redirect('home')
	member = ArchiveMember.objects.get(id=archive_member_id)
	buf = member.fetch_from_zip()
	return HttpResponse(buf, mimetype=member.guess_mime_type())


@writeable_site_required
def resolve_screenshot(request, productionlink_id, archive_member_id):
	if not request.user.is_staff:
		return redirect('home')
	production_link = ProductionLink.objects.get(id=productionlink_id)
	archive_member = ArchiveMember.objects.get(id=archive_member_id)

	if request.POST:
		production_link.file_for_screenshot = archive_member.filename
		production_link.is_unresolved_for_screenshotting = False
		production_link.save()
		create_screenshot_from_production_link.delay(productionlink_id)
	return HttpResponse('OK', mimetype='text/plain')


def results_with_no_encoding(request):
	if not request.user.is_staff:
		return redirect('home')
	results_files = ResultsFile.objects.filter(encoding__isnull=True).select_related('party').order_by('party__start_date_date')

	return render(request, 'maintenance/results_with_no_encoding.html', {
		'title': 'Results files with unknown character encoding',
		'results_files': results_files,
	})

ENCODING_OPTIONS = [
	('Common encodings', [
		('iso-8859-1', 'Western (ISO-8859-1)'),
		('iso-8859-2', 'Central European (ISO-8859-2)'),
		('iso-8859-3', 'South European (ISO-8859-3)'),
		('iso-8859-4', 'Baltic (ISO-8859-4)'),
		('iso-8859-5', 'Cyrillic (ISO-8859-5)'),
		('cp437', 'MS-DOS (CP437)'),
		('cp866', 'MS-DOS Cyrillic (CP866)'),
		('koi8_r', 'Cyrillic Russian (KOI8-R)'),
		('koi8_u', 'Cyrillic Ukrainian (KOI8-U)'),
		('windows-1250', 'Central European (Windows-1250)'),
		('windows-1251', 'Cyrillic (Windows-1251)'),
		('windows-1252', 'Western (Windows-1252)'),
	]),
	('Obscure encodings', [
		('big5', 'Chinese Traditional (Big5)'),
		('big5-hkscs', 'Chinese Traditional (Big5-HKSCS)'),
		('cp737', 'MS-DOS Greek (CP737)'),
		('cp775', 'MS-DOS Baltic Rim (CP775)'),
		('cp850', 'MS-DOS Latin 1 (CP850)'),
		('cp852', 'MS-DOS Latin 2 (CP852)'),
		('cp855', 'MS-DOS Cyrillic (CP855)'),
		('cp856', 'Hebrew (CP856)'),
		('cp857', 'MS-DOS Turkish (CP857)'),
		('cp860', 'MS-DOS Portuguese (CP860)'),
		('cp861', 'MS-DOS Icelandic (CP861)'),
		('cp862', 'MS-DOS Hebrew (CP862)'),
		('cp863', 'MS-DOS French Canada (CP863)'),
		('cp864', 'Arabic (CP864)'),
		('cp865', 'MS-DOS Nordic (CP865)'),
		('cp869', 'MS-DOS Greek 2 (CP869)'),
		('cp874', 'Thai (CP874)'),
		('cp932', 'Japanese (CP932)'),
		('cp949', 'Korean (CP949)'),
		('cp950', 'Chinese Traditional (CP949)'),
		('cp1006', 'Urdu (CP1006)'),
		('euc_jp', 'Japanese (EUC-JP)'),
		('euc_jis_2004', 'Japanese (EUC-JIS-2004)'),
		('euc_jisx0213', 'Japanese (EUC-JIS-X-0213)'),
		('euc_kr', 'Korean (EUC-KR)'),
		('gb2312', 'Chinese Simplified (GB 2312)'),
		('gbk', 'Chinese Simplified (GBK)'),
		('gb18030', 'Chinese Simplified (GB 18030)'),
		('hz', 'Chinese Simplified (HZ)'),
		('iso-2022-jp', 'Japanese (ISO-2022-JP)'),
		('iso-2022-jp-1', 'Japanese (ISO-2022-JP-1)'),
		('iso-2022-jp-2', 'Japanese (ISO-2022-JP-2)'),
		('iso-2022-jp-2004', 'Japanese (ISO-2022-JP-2004)'),
		('iso-2022-jp-3', 'Japanese (ISO-2022-JP-3)'),
		('iso-2022-jp-ext', 'Japanese (ISO-2022-JP-EXT)'),
		('iso-2022-kr', 'Korean (ISO-2022-KR)'),
		('iso-8859-6', 'Arabic (ISO-8859-6)'),
		('iso-8859-7', 'Greek (ISO-8859-7)'),
		('iso-8859-8', 'Hebrew (ISO-8859-8)'),
		('iso-8859-9', 'Turkish (ISO-8859-9)'),
		('iso-8859-10', 'Nordic (ISO-8859-10)'),
		('iso-8859-13', 'Baltic (ISO-8859-13)'),
		('iso-8859-14', 'Celtic (ISO-8859-14)'),
		('iso-8859-15', 'Western (ISO-8859-15)'),
		('johab', 'Korean (Johab)'),
		('mac_cyrillic', 'Cyrillic (Macintosh)'),
		('mac_greek', 'Greek (Macintosh)'),
		('mac_iceland', 'Icelandic (Macintosh)'),
		('mac_latin2', 'Central European (Macintosh)'),
		('mac_roman', 'Western (Macintosh)'),
		('mac_turkish', 'Turkish (Macintosh)'),
		('shift_jis', 'Japanese (Shift_JIS)'),
		('shift_jis_2004', 'Japanese (Shift_JIS_2004)'),
		('shift_jisx0213', 'Japanese (Shift_JIS_X_0213)'),
		('windows-1253', 'Greek (Windows-1253)'),
		('windows-1254', 'Turkish (Windows-1254)'),
		('windows-1255', 'Hebrew (Windows-1255)'),
		('windows-1256', 'Arabic (Windows-1256)'),
		('windows-1257', 'Baltic (Windows-1257)'),
		('windows-1258', 'Vietnamese (Windows-1258)'),
	]),
]

def fix_results_file_encoding(request, results_file_id):
	if not request.user.is_staff:
		return redirect('home')
	results_file = get_object_or_404(ResultsFile, id=results_file_id)
	if request.POST:
		encoding = request.POST['encoding']
	else:
		encoding = request.GET.get('encoding', 'iso-8859-1')

	# check that the encoding is one that we recognise
	try:
		''.decode(encoding)
	except LookupError:
		encoding = 'iso-8859-1'

	file_lines = []
	encoding_is_valid = True

	for line in results_file.file:
		try:
			line.decode('ascii')
			is_ascii = True
		except UnicodeDecodeError:
			is_ascii = False

		try:
			decoded_line = line.decode(encoding)
			file_lines.append((is_ascii, True, decoded_line))
		except UnicodeDecodeError:
			encoding_is_valid = False
			file_lines.append((is_ascii, False, line.decode('iso-8859-1')))

	if request.POST:
		if encoding_is_valid:
			results_file.encoding = encoding
			results_file.save()
		return redirect('maintenance_results_with_no_encoding')
	return render(request, 'maintenance/fix_results_file_encoding.html', {
		'results_file': results_file,
		'party': results_file.party,
		'file_lines': file_lines,
		'encoding_is_valid': encoding_is_valid,
		'encoding': encoding,
		'encoding_options': ENCODING_OPTIONS,
	})
