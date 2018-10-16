from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic.base import TemplateView

from fuzzy_date import FuzzyDate
from read_only_mode import writeable_site_required

from demoscene.models import Nick, Releaser, Membership, ReleaserExternalLink
from comments.models import Comment
from parties.models import Competition, PartyExternalLink, Party, ResultsFile
from productions.models import Production, Credit, ProductionLink, ProductionBlurb, ProductionType
from sceneorg.models import Directory
from maintenance import reports as reports_module
from maintenance.forms import ProductionFilterForm
from maintenance.models import Exclusion
from mirror.models import ArchiveMember
from screenshots.tasks import create_screenshot_from_production_link


def index(request):
	return render(request, 'maintenance/index.html', {
		'reports': reports if request.user.is_staff else public_reports,
	})


class StaffOnlyMixin(object):
	is_staff_only = True

	def dispatch(self, request, *args, **kwargs):
		if not request.user.is_staff:
			return redirect('home')
		return super(StaffOnlyMixin, self).dispatch(request, *args, **kwargs)


class Report(TemplateView):
	title = 'Untitled report :-('

	@property
	def exclusion_name(self):
		return self.name

	@classmethod
	def get_url(cls):
		return reverse('maintenance:%s' % cls.name)

	@classmethod
	def get_urlpattern(cls):
		return url('^%s$' % cls.name, cls.as_view(), name=cls.name)

	def get_context_data(self, **kwargs):
		context = super(Report, self).get_context_data(**kwargs)
		context['title'] = self.title
		context['report_name'] = self.name
		context['exclusion_name'] = self.exclusion_name
		return context


class FilterableProductionReport(Report):
	template_name = 'maintenance/filtered_production_report.html'
	limit = 100

	def get_context_data(self, **kwargs):
		context = super(FilterableProductionReport, self).get_context_data(**kwargs)

		filter_form = ProductionFilterForm(self.request.GET)
		if filter_form.is_valid():
			platform_ids = [platform.id for platform in filter_form.cleaned_data['platform']]
			prod_type_ids = [typ.id for typ in filter_form.cleaned_data['production_type']]
		else:
			platform_ids = []
			prod_type_ids = []

		productions, total_count = self.report_class.run(
			limit=self.limit, platform_ids=platform_ids, production_type_ids=prod_type_ids
		)

		context.update({
			'productions': productions,
			'mark_excludable': self.request.user.is_staff,
			'total_count': total_count,
			'count': len(productions),
			'filter_form': filter_form,
			'url': self.get_url(),
		})
		return context


class ProdsWithoutScreenshots(FilterableProductionReport):
	title = "Productions without screenshots"
	name = 'prods_without_screenshots'
	report_class = reports_module.ProductionsWithoutScreenshotsReport


class ProdsWithoutVideoCaptures(FilterableProductionReport):
	title = "Productions without video captures"
	name = 'prods_without_videos'
	report_class = reports_module.ProductionsWithoutVideosReport


class ProdsWithoutCredits(FilterableProductionReport):
	title = "Productions without individual credits"
	name = 'prods_without_credits'
	report_class = reports_module.ProductionsWithoutCreditsReport


class RandomisedProductionReport(Report):
	template_name = 'maintenance/randomised_production_report.html'
	limit = 100

	def get_context_data(self, **kwargs):
		context = super(RandomisedProductionReport, self).get_context_data(**kwargs)

		productions, total_count = self.report_class.run(limit=self.limit)

		context.update({
			'productions': productions,
			'mark_excludable': self.request.user.is_staff,
			'total_count': total_count,
			'count': len(productions),
		})
		return context


class TrackedMusicWithoutPlayableLinks(RandomisedProductionReport):
	title = "Tracked music without playable links"
	name = 'tracked_music_without_playable_links'
	report_class = reports_module.TrackedMusicWithoutPlayableLinksReport


class ProdsWithoutExternalLinks(StaffOnlyMixin, Report):
	title = "Productions without external links"
	template_name = 'maintenance/production_report.html'
	name = 'prods_without_external_links'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutExternalLinks, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithoutReleaseDate(StaffOnlyMixin, Report):
	title = "Productions without a release date"
	template_name = 'maintenance/production_report.html'
	name = 'prods_without_release_date'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutReleaseDate, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(release_date_date__isnull=True)
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithDeadAmigascneLinks(StaffOnlyMixin, Report):
	title = "Productions with dead amigascne links"
	template_name = 'maintenance/production_report.html'
	name = 'prods_with_dead_amigascne_links'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithDeadAmigascneLinks, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(links__parameter__contains='amigascne.org/old/')
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithDeadAmigaNvgOrgLinks(StaffOnlyMixin, Report):
	title = "Productions with dead amiga.nvg.org links"
	template_name = 'maintenance/production_report.html'
	name = 'prods_with_dead_amiga_nvg_org_links'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithDeadAmigaNvgOrgLinks, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(links__parameter__contains='amiga.nvg.org')
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class SceneorgDownloadLinksWithUnicode(StaffOnlyMixin, Report):
	title = "scene.org download links with unicode characters"
	template_name = 'maintenance/production_report.html'
	name = 'sceneorg_download_links_with_unicode'

	def get_context_data(self, **kwargs):
		context = super(SceneorgDownloadLinksWithUnicode, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(links__is_download_link=True, links__link_class='SceneOrgFile')
			.extra(
				where=["not productions_productionlink.parameter ~ '^[\x20-\x7E]+$'"],
			).distinct().prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').defer('notes').order_by('title')
		)
		context.update({
			'productions': productions,
			# don't implement exclusions on this report, because it's possible that a URL containing unicode
			# that works now will be broken in future, and we don't want those cases to be hidden through
			# exclusions
			'mark_excludable': False,
		})
		return context


class ProdsWithoutPlatforms(StaffOnlyMixin, Report):
	title = "Productions without platforms"
	template_name = 'maintenance/production_report.html'
	name = 'prods_without_platforms'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutPlatforms, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(platforms__isnull=True, supertype='production')
			.exclude(types__name__in=('Video', 'Performance'))
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithoutPlatformsExcludingLost(StaffOnlyMixin, Report):
	title = "Productions without platforms (excluding 'lost')"
	template_name = 'maintenance/production_report.html'
	exclusion_name = 'prods_without_platforms'  # share the exclusion list with the main prods_without_platforms report
	name = 'prods_without_platforms_excluding_lost'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutPlatformsExcludingLost, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(platforms__isnull=True, supertype='production')
			.exclude(types__name__in=('Video', 'Performance'))
			.exclude(tags__name=('lost'))
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithoutPlatformsWithDownloads(StaffOnlyMixin, Report):
	title = "Productions without platforms (with downloads)"
	template_name = 'maintenance/production_report.html'
	exclusion_name = 'prods_without_platforms'  # share the exclusion list with the main prods_without_platforms report
	name = 'prods_without_platforms_with_downloads'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutPlatformsWithDownloads, self).get_context_data(**kwargs)

		productions = (
			Production.objects.filter(platforms__isnull=True, supertype='production')
			.filter(links__is_download_link=True)
			.exclude(types__name__in=('Video', 'Performance'))
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class ProdsWithoutReleaseDateWithPlacement(StaffOnlyMixin, Report):
	title = "Productions without a release date but with a party placement attached"
	template_name = 'maintenance/production_release_date_report.html'
	name = 'prods_without_release_date_with_placement'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithoutReleaseDateWithPlacement, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])

		productions = list(productions)
		for production in productions:
			production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
		context.update({
			'productions': productions,
			'return_to': reverse('maintenance:prods_without_release_date_with_placement'),
		})
		return context


class ProdSoundtracksWithoutReleaseDate(StaffOnlyMixin, Report):
	title = "Music with productions attached but no release date"
	template_name = 'maintenance/production_release_date_report.html'
	name = 'prod_soundtracks_without_release_date'

	def get_context_data(self, **kwargs):
		context = super(ProdSoundtracksWithoutReleaseDate, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])
		productions = list(productions)
		for production in productions:
			if production.suggested_release_date_date is not None:
				production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)
		context.update({
			'productions': productions,
			'return_to': reverse('maintenance:prod_soundtracks_without_release_date'),
		})
		return context


class GroupNicksWithBrackets(StaffOnlyMixin, Report):
	title = "Group names with brackets"
	template_name = 'maintenance/nick_report.html'
	name = 'group_nicks_with_brackets'

	def get_context_data(self, **kwargs):
		context = super(GroupNicksWithBrackets, self).get_context_data(**kwargs)

		nicks = (
			Nick.objects.filter(name__contains='(', releaser__is_group=True)
			.extra(
				where=['demoscene_nick.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).order_by('name')
		)
		context.update({
			'nicks': nicks,
		})
		return context


class AmbiguousGroupsWithNoDifferentiators(StaffOnlyMixin, Report):
	title = "Ambiguous group names with no differentiators"
	template_name = 'maintenance/ambiguous_group_names.html'
	name = 'ambiguous_groups_with_no_differentiators'

	def get_context_data(self, **kwargs):
		context = super(AmbiguousGroupsWithNoDifferentiators, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])
		context.update({
			'nicks': nicks,
		})
		return context


class ProdsWithReleaseDateOutsideParty(StaffOnlyMixin, Report):
	title = "Productions with a release date more than 14 days away from their release party"
	template_name = 'maintenance/production_release_date_report.html'
	name = 'prods_with_release_date_outside_party'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithReleaseDateOutsideParty, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])
		productions = list(productions)
		for production in productions:
			production.suggested_release_date = FuzzyDate(production.suggested_release_date_date, production.suggested_release_date_precision)

		context.update({
			'productions': productions,
			'return_to': reverse('maintenance:prods_with_release_date_outside_party'),
		})
		return context


class ProdsWithSameNamedCredits(StaffOnlyMixin, Report):
	title = "Productions with identically-named sceners in the credits"
	template_name = 'maintenance/production_report.html'
	name = 'prods_with_same_named_credits'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithSameNamedCredits, self).get_context_data(**kwargs)

		productions = Production.objects.raw('''
			SELECT DISTINCT productions_production.*
			FROM productions_production
			INNER JOIN productions_credit ON (productions_production.id = productions_credit.production_id)
			INNER JOIN demoscene_nick ON (productions_credit.nick_id = demoscene_nick.id)
			INNER JOIN demoscene_nick AS other_nick ON (demoscene_nick.name = other_nick.name AND demoscene_nick.id <> other_nick.id)
			INNER JOIN productions_credit AS other_credit ON (other_nick.id = other_credit.nick_id AND other_credit.production_id = productions_production.id)
			AND productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)
		''', [self.exclusion_name])

		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class SameNamedProdsBySameReleaser(StaffOnlyMixin, Report):
	title = "Identically-named productions by the same releaser"
	template_name = 'maintenance/production_report.html'
	name = 'same_named_prods_by_same_releaser'

	def get_context_data(self, **kwargs):
		context = super(SameNamedProdsBySameReleaser, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])

		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class SameNamedProdsWithoutSpecialChars(StaffOnlyMixin, Report):
	title = "Identically-named productions by the same releaser, ignoring special chars"
	template_name = 'maintenance/production_report.html'
	name = 'same_named_prods_without_special_chars'

	def get_context_data(self, **kwargs):
		context = super(SameNamedProdsWithoutSpecialChars, self).get_context_data(**kwargs)

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

		context.update({
			'productions': productions,
			'mark_excludable': True,
		})
		return context


class DuplicateExternalLinks(StaffOnlyMixin, Report):
	title = "Duplicate external links"
	template_name = 'maintenance/duplicate_external_links.html'
	name = 'duplicate_external_links'

	def get_context_data(self, **kwargs):
		context = super(DuplicateExternalLinks, self).get_context_data(**kwargs)
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
					AND other_link.is_download_link = 'f'
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

		context.update({
			'prod_dupes': prod_dupes,
			'releaser_dupes': releaser_dupes,
		})
		return context


class MatchingRealNames(StaffOnlyMixin, Report):
	title = "Sceners with matching real names"
	template_name = 'maintenance/matching_real_names.html'
	name = 'matching_real_names'

	def get_context_data(self, **kwargs):
		context = super(MatchingRealNames, self).get_context_data(**kwargs)

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
		context.update({
			'releasers': releasers,
		})
		return context


class MatchingSurnames(StaffOnlyMixin, Report):
	title = "Sceners with matching surnames"
	template_name = 'maintenance/matching_surnames.html'
	name = 'matching_surnames'

	def get_context_data(self, **kwargs):
		context = super(MatchingSurnames, self).get_context_data(**kwargs)

		releasers = Releaser.objects.raw('''
			SELECT DISTINCT demoscene_releaser.*
			FROM demoscene_releaser
			INNER JOIN demoscene_releaser AS other_releaser ON (
				demoscene_releaser.surname <> ''
				AND demoscene_releaser.surname = other_releaser.surname
				AND demoscene_releaser.id <> other_releaser.id)
			ORDER BY demoscene_releaser.surname, demoscene_releaser.first_name, demoscene_releaser.name
		''')
		context.update({
			'releasers': releasers,
		})
		return context


class ImpliedMemberships(StaffOnlyMixin, Report):
	title = "Group memberships found in production bylines, but missing from the member list"
	template_name = 'maintenance/implied_memberships.html'
	name = 'implied_memberships'

	def get_context_data(self, **kwargs):
		context = super(ImpliedMemberships, self).get_context_data(**kwargs)

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
		context.update({
			'records': records,
		})
		return context


class GroupsWithSameNamedMembers(StaffOnlyMixin, Report):
	title = "Groups with same-named members"
	template_name = 'maintenance/groups_with_same_named_members.html'
	name = 'groups_with_same_named_members'

	def get_context_data(self, **kwargs):
		context = super(GroupsWithSameNamedMembers, self).get_context_data(**kwargs)
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
		context.update({
			'groups': groups,
		})
		return context


class ReleasersWithSameNamedGroups(StaffOnlyMixin, Report):
	title = "Releasers with same-named groups"
	template_name = 'maintenance/releasers_with_same_named_groups.html'
	name = 'releasers_with_same_named_groups'

	def get_context_data(self, **kwargs):
		context = super(ReleasersWithSameNamedGroups, self).get_context_data(**kwargs)
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
		context.update({
			'releasers': releasers,
		})
		return context


class SceneorgPartyDirsWithNoParty(StaffOnlyMixin, Report):
	title = "scene.org party dirs which are not linked to a party"
	template_name = 'maintenance/sceneorg_party_dirs_with_no_party.html'
	name = 'sceneorg_party_dirs_with_no_party'

	def get_context_data(self, **kwargs):
		context = super(SceneorgPartyDirsWithNoParty, self).get_context_data(**kwargs)

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

		context.update({
			'directories': directories,
			'total_count': total_count,
			'matched_count': matched_count,
		})
		return context


class PartiesWithIncompleteDates(StaffOnlyMixin, Report):
	title = "Parties with incomplete dates"
	template_name = 'maintenance/party_report.html'
	name = 'parties_with_incomplete_dates'

	def get_context_data(self, **kwargs):
		context = super(PartiesWithIncompleteDates, self).get_context_data(**kwargs)
		parties = Party.objects.extra(
			where=[
				"(start_date_precision <> 'd' OR end_date_precision <> 'd')",
				"parties_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
			],
			params=[self.exclusion_name]
		).order_by('start_date_date')

		context.update({
			'parties': parties,
		})
		return context


class PartiesWithNoLocation(StaffOnlyMixin, Report):
	title = "Parties with no location"
	template_name = 'maintenance/party_report.html'
	name = 'parties_with_no_location'

	def get_context_data(self, **kwargs):
		context = super(PartiesWithNoLocation, self).get_context_data(**kwargs)
		parties = Party.objects.extra(
			where=[
				"latitude IS NULL",
				"is_online = 'f'",
				"parties_party.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)"
			],
			params=[self.exclusion_name]
		).order_by('start_date_date')

		context.update({
			'parties': parties,
		})
		return context


class EmptyReleasers(StaffOnlyMixin, Report):
	title = "Empty releaser records"
	template_name = 'maintenance/releaser_report.html'
	name = 'empty_releasers'

	def get_context_data(self, **kwargs):
		context = super(EmptyReleasers, self).get_context_data(**kwargs)
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
		''', [self.exclusion_name])

		context.update({
			'releasers': releasers,
		})
		return context


class EmptyCompetitions(StaffOnlyMixin, Report):
	title = "Empty competitions"
	template_name = 'maintenance/competition_report.html'
	name = 'empty_competitions'

	def get_context_data(self, **kwargs):
		context = super(EmptyCompetitions, self).get_context_data(**kwargs)
		competitions = Competition.objects.filter(
			placings__isnull=True
		).extra(
			where=['parties_competition.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
			params=[self.exclusion_name]
		).select_related('party').order_by('party__start_date_date')

		context.update({
			'competitions': competitions,
		})
		return context


class UnresolvedScreenshots(StaffOnlyMixin, Report):
	title = "Unresolved screenshots"
	template_name = 'maintenance/unresolved_screenshots.html'
	name = 'unresolved_screenshots'

	def get_context_data(self, **kwargs):
		context = super(UnresolvedScreenshots, self).get_context_data(**kwargs)
		links = ProductionLink.objects.filter(is_unresolved_for_screenshotting=True, production__screenshots__isnull=True).select_related('production')

		entries = []
		for link in links[:100]:
			entries.append((
				link,
				link.archive_members().filter(file_size__gt=0).exclude(filename__in=['scene.org', 'scene.org.txt'])
			))

		context.update({
			'link_count': links.count(),
			'entries': entries,
		})
		return context


class PublicRealNames(StaffOnlyMixin, Report):
	title = "Sceners with public real names"
	template_name = 'maintenance/public_real_names.html'
	name = 'public_real_names'

	def get_context_data(self, **kwargs):
		context = super(PublicRealNames, self).get_context_data(**kwargs)

		has_public_first_name = (~Q(first_name='')) & Q(show_first_name=True)
		has_public_surname = (~Q(surname='')) & Q(show_surname=True)

		sceners = Releaser.objects.filter(
			Q(is_group=False),
			has_public_first_name | has_public_surname
		).order_by('name')

		if self.request.GET.get('without_note'):
			sceners = sceners.filter(real_name_note='')

		context.update({
			'sceners': sceners,
		})
		return context


class ProdsWithBlurbs(StaffOnlyMixin, Report):
	title = "Productions with blurbs"
	template_name = 'maintenance/prods_with_blurbs.html'
	name = 'prods_with_blurbs'

	def get_context_data(self, **kwargs):
		context = super(ProdsWithBlurbs, self).get_context_data(**kwargs)

		blurbs = ProductionBlurb.objects.select_related('production')

		context.update({
			'blurbs': blurbs,
		})
		return context


class ProdComments(StaffOnlyMixin, Report):
	title = "Latest production comments"
	template_name = 'maintenance/prod_comments.html'
	name = 'prod_comments'

	def get_context_data(self, **kwargs):
		context = super(ProdComments, self).get_context_data(**kwargs)

		production_type = ContentType.objects.get_for_model(Production)

		comments = Comment.objects.filter(content_type=production_type).order_by('-created_at').select_related('user')
		paginator = Paginator(comments, 100)

		page = self.request.GET.get('page', 1)
		try:
			comments_page = paginator.page(page)
		except (PageNotAnInteger, EmptyPage):
			# If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
			comments_page = paginator.page(paginator.num_pages)

		context.update({
			'comments': comments_page,
		})
		return context


class CreditsToMoveToText(StaffOnlyMixin, Report):
	title = "Credits that probably need to be moved to the Text category"
	template_name = 'maintenance/credits_to_move_to_text.html'
	name = 'credits_to_move_to_text'

	def get_context_data(self, **kwargs):
		context = super(CreditsToMoveToText, self).get_context_data(**kwargs)

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
		''', [self.exclusion_name])

		context.update({
			'credits': credits,
			'mark_excludable': True,
		})
		return context


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
	return HttpResponse('OK', content_type='text/plain')


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
	return HttpResponse('OK', content_type='text/plain')


@writeable_site_required
def add_sceneorg_link_to_party(request):
	if not request.user.is_staff:
		return redirect('home')
	if request.POST and request.POST.get('path') and request.POST.get('party_id'):
		PartyExternalLink.objects.create(
			party_id=request.POST['party_id'],
			parameter=request.POST['path'],
			link_class='SceneOrgFolder')
	return HttpResponse('OK', content_type='text/plain')


def view_archive_member(request, archive_member_id):
	if not request.user.is_staff:
		return redirect('home')
	member = ArchiveMember.objects.get(id=archive_member_id)
	buf = member.fetch_from_zip()
	return HttpResponse(buf, content_type=member.guess_mime_type())


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
	return HttpResponse('OK', content_type='text/plain')


class ResultsWithNoEncoding(StaffOnlyMixin, Report):
	title = "Results files with unknown character encoding"
	template_name = 'maintenance/results_with_no_encoding.html'
	name = 'results_with_no_encoding'

	def get_context_data(self, **kwargs):
		context = super(ResultsWithNoEncoding, self).get_context_data(**kwargs)
		results_files = ResultsFile.objects.filter(encoding__isnull=True).select_related('party').order_by('party__start_date_date')

		context.update({
			'results_files': results_files,
		})
		return context

ENCODING_OPTIONS = [
	(
		'Common encodings',
		[
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
		]
	),
	(
		'Obscure encodings',
		[
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
		]
	),
]


@writeable_site_required
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
		return redirect('maintenance:results_with_no_encoding')
	return render(request, 'maintenance/fix_results_file_encoding.html', {
		'results_file': results_file,
		'party': results_file.party,
		'file_lines': file_lines,
		'encoding_is_valid': encoding_is_valid,
		'encoding': encoding,
		'encoding_options': ENCODING_OPTIONS,
	})


class TinyIntrosWithoutDownloadLinks(Report):
	title = "Tiny intros without download links"
	template_name = 'maintenance/production_report.html'
	name = 'tiny_intros_without_download_links'

	def get_context_data(self, **kwargs):
		context = super(TinyIntrosWithoutDownloadLinks, self).get_context_data(**kwargs)

		prod_types = list(ProductionType.objects.filter(name__in=[
			'32b Intro', '64b Intro', '128b Intro', '512b Intro', '1K Intro', '2K Intro', '4K Intro'
		]))

		intros = Production.objects.filter(supertype='production', types__in=prod_types)
		intros_with_download_links = intros.filter(links__is_download_link=True).distinct().values_list('id', flat=True)

		productions = (
			intros.exclude(id__in=intros_with_download_links)
			.extra(
				where=['productions_production.id NOT IN (SELECT record_id FROM maintenance_exclusion WHERE report_name = %s)'],
				params=[self.exclusion_name]
			).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser').order_by('title')
		)
		context.update({
			'productions': productions,
			'mark_excludable': self.request.user.is_staff,
		})
		return context


class ExternalReport(object):
	# placeholder for an item in the reports menu that doesn't live here
	def __init__(self, url_name, title):
		self.url_name = url_name
		self.title = title

	def get_url(self):
		return reverse(self.url_name)


reports = [
	(
		"Supporting data",
		[
			ProdsWithoutExternalLinks,
			ProdsWithoutScreenshots,
			ProdsWithoutVideoCaptures,
			ProdsWithoutCredits,
			ProdsWithoutPlatforms,
			ProdsWithoutPlatformsExcludingLost,
			ProdsWithoutPlatformsWithDownloads,
			TrackedMusicWithoutPlayableLinks,
			UnresolvedScreenshots,
			ProdsWithBlurbs,
			TinyIntrosWithoutDownloadLinks,
			ExternalReport('pouet_groups', "Pouet link matching"),
		]
	),
	(
		"Release dates",
		[
			ProdsWithoutReleaseDate,
			ProdsWithoutReleaseDateWithPlacement,
			ProdsWithReleaseDateOutsideParty,
			ProdSoundtracksWithoutReleaseDate,
		]
	),
	(
		"Cleanup",
		[
			GroupNicksWithBrackets,
			AmbiguousGroupsWithNoDifferentiators,
			ImpliedMemberships,
			EmptyReleasers,
			PublicRealNames,
			ProdsWithDeadAmigascneLinks,
			ProdsWithDeadAmigaNvgOrgLinks,
			CreditsToMoveToText,
			SceneorgDownloadLinksWithUnicode,
			EmptyCompetitions,
		]
	),
	(
		"De-duping",
		[
			ProdsWithSameNamedCredits,
			SameNamedProdsBySameReleaser,
			SameNamedProdsWithoutSpecialChars,
			DuplicateExternalLinks,
			MatchingRealNames,
			MatchingSurnames,
			GroupsWithSameNamedMembers,
			ReleasersWithSameNamedGroups,
		]
	),
	(
		"Parties",
		[
			SceneorgPartyDirsWithNoParty,
			PartiesWithIncompleteDates,
			PartiesWithNoLocation,
			ExternalReport('sceneorg_compofolders', "scene.org competition directory matching"),
			ExternalReport('sceneorg_compofiles', "scene.org party file matching"),
			ResultsWithNoEncoding,
		]
	),
	(
		"User activity",
		[
			ProdComments,
		]
	),
]

public_reports = []
for heading, section_reports in reports:
	public_section_reports = [r for r in section_reports if not getattr(r, 'is_staff_only', False)]
	if public_section_reports:
		public_reports.append((heading, public_section_reports))
