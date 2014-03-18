from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import math

from demoscene.models import Production, Screenshot, ProductionLink, Releaser, ReleaserExternalLink, Membership, Credit
from parties.models import Party
from zxdemo.models import NewsItem, spectrum_releasers, filter_releasers_queryset_to_spectrum

def home(request):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	cursor = connection.cursor()
	cursor.execute(
		"""
			SELECT COUNT(DISTINCT demoscene_nick.releaser_id)
			FROM demoscene_nick
			WHERE demoscene_nick.id IN (
				SELECT DISTINCT demoscene_production_author_nicks.nick_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_production_author_nicks ON (demoscene_production_platforms.production_id = demoscene_production_author_nicks.production_id)
				WHERE demoscene_production_platforms.platform_id IN (%s)
			)
			OR demoscene_nick.id IN (
				SELECT DISTINCT demoscene_production_author_affiliation_nicks.nick_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production_platforms.production_id = demoscene_production_author_affiliation_nicks.production_id)
				WHERE demoscene_production_platforms.platform_id IN (%s)
			)
			OR demoscene_nick.id IN (
				SELECT DISTINCT demoscene_credit.nick_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_credit ON (demoscene_production_platforms.production_id = demoscene_credit.production_id)
				WHERE demoscene_production_platforms.platform_id IN (%s)
			)
		""", [tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS)]
	)
	releaser_count = cursor.fetchone()[0]

	random_screenshot = Screenshot.objects.filter(production__platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('?')[0]

	latest_releases = Production.objects.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS, release_date_date__isnull=False).order_by('-release_date_date').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')[:10]
	latest_additions = Production.objects.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('-created_at').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')[:10]

	news_items = NewsItem.objects.order_by('-created_at').select_related('author')[:8]

	return render(request, 'zxdemo/home.html', {
		'stats': {
			'demo_count': Production.objects.filter(supertype='production', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
			'music_count': Production.objects.filter(supertype='music', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
			'graphics_count': Production.objects.filter(supertype='graphics', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
			'releaser_count': releaser_count,
		},
		'random_screenshot': random_screenshot,
		'latest_releases': latest_releases,
		'latest_additions': latest_additions,
		'news_items': news_items,
	})


def show_screenshot(request, screenshot_id):
	screenshot = get_object_or_404(Screenshot, id=screenshot_id)
	return render(request, 'zxdemo/show_screenshot.html', {
		'screenshot': screenshot,
		'production': screenshot.production,
	})


def productions(request):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	productions = Production.objects.filter(
		platforms__id__in=ZXDEMO_PLATFORM_IDS
	).extra(select={'lower_title': 'lower(demoscene_production.title)'}).order_by('lower_title').prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

	supertypes = []
	if request.GET.get('demos', '1'):
		supertypes.append('production')
	if request.GET.get('music', '1'):
		supertypes.append('music')
	if request.GET.get('graphics', '1'):
		supertypes.append('graphics')

	productions = productions.filter(supertype__in=supertypes)
	if request.GET.get('noscreen'):
		productions=productions.filter(screenshots__id__isnull=True)

	count = request.GET.get('count', '50')
	letter = request.GET.get('letter', '')
	if len(letter) == 1 and letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
		productions = productions.filter(title__istartswith=letter)

	paginator = Paginator(productions, int(count))
	page = request.GET.get('page')

	try:
		productions_page = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page of results.
		productions_page = paginator.page(1)
	except EmptyPage:
		# If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
		productions_page = paginator.page(paginator.num_pages)

	return render(request, 'zxdemo/productions.html', {
		'productions': productions_page,
		'count': count,
		'letters': '#ABCDEFGHIJKLMNOPQRSTUVWXYZ',
		'count_options': ['10', '25', '50', '75', '100', '150', '200'],
		'filters': {
			'demos': 'production' in supertypes,
			'graphics': 'graphics' in supertypes,
			'music': 'music' in supertypes,
		},
	})

def production(request, production_id):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	production = get_object_or_404(Production, id=production_id, platforms__id__in=ZXDEMO_PLATFORM_IDS)

	try:
		random_screenshot = production.screenshots.order_by('?')[0]
	except IndexError:
		random_screenshot = None

	return render(request, 'zxdemo/production.html', {
		'production': production,
		'competition_placings': production.competition_placings.select_related('competition__party').order_by('competition__party__start_date_date'),
		'credits': production.credits_for_listing(),
		'screenshot': random_screenshot,
		'download_links': production.links.filter(is_download_link=True),
	})

def production_redirect(request):
	prod_link = get_object_or_404(ProductionLink, link_class='ZxdemoItem', parameter=request.GET.get('id'))
	return redirect('zxdemo_production', prod_link.production_id, permanent=True)


def authors(request):
	releasers = spectrum_releasers().extra(select={'lower_name': 'lower(demoscene_releaser.name)'}).order_by('lower_name')
	count = request.GET.get('count', '50')
	letter = request.GET.get('letter', '')
	if len(letter) == 1 and letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
		releasers = releasers.filter(name__istartswith=letter)

	paginator = Paginator(releasers, int(count))
	page = request.GET.get('page')

	try:
		releasers_page = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page of results.
		releasers_page = paginator.page(1)
	except EmptyPage:
		# If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
		releasers_page = paginator.page(paginator.num_pages)

	return render(request, 'zxdemo/authors.html', {
		'releasers': releasers_page,
		'count': count,
		'letters': '#ABCDEFGHIJKLMNOPQRSTUVWXYZ',
		'count_options': ['10', '25', '50', '75', '100', '150', '200'],
	})


def author(request, releaser_id):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

	try:
		releaser = spectrum_releasers().get(id=releaser_id)
	except Releaser.DoesNotExist:
		raise Http404

	if releaser.is_group:
		member_memberships = filter_releasers_queryset_to_spectrum(
			releaser.member_memberships.select_related('member'),
			releaser_table='T3'
		)
	else:
		member_memberships = Membership.objects.none()

	group_memberships = filter_releasers_queryset_to_spectrum(
		releaser.group_memberships.select_related('group'),
		releaser_table='T3'
	)

	release_author_filter = Q(author_nicks__releaser=releaser) | Q(author_affiliation_nicks__releaser=releaser)
	releases = Production.objects.filter(
		release_author_filter,
		platforms__id__in=ZXDEMO_PLATFORM_IDS
	).order_by('release_date_date').distinct().prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

	credits = Credit.objects.filter(
		nick__releaser=releaser,
		production__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).order_by('production__release_date_date', 'production__title', 'production__id').prefetch_related('production__links', 'production__screenshots', 'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser')

	if request.GET.get('noscreen'):
		releases=releases.exclude(supertype='music').filter(screenshots__id__isnull=True)
		credits=credits.exclude(production__supertype='music').filter(production__screenshots__id__isnull=True)

	releases_by_id = {}
	releases_with_credits = []
	for prod in releases:
		release_record = {'production': prod, 'credits': []}
		releases_by_id[prod.id] = release_record
		releases_with_credits.append(release_record)

	non_releaser_credits = []
	for credit in credits:
		if credit.production_id in releases_by_id:
			releases_by_id[credit.production_id]['credits'].append(credit)
		else:
			non_releaser_credits.append(credit)

	return render(request, 'zxdemo/author.html', {
		'releaser': releaser,
		'member_memberships': member_memberships,
		'group_memberships': group_memberships,
		'releases_with_credits': releases_with_credits,
		'non_releaser_credits': non_releaser_credits,
	})

def author_redirect(request):
	releaser_link = get_object_or_404(ReleaserExternalLink, link_class='ZxdemoAuthor', parameter=request.GET.get('id'))
	return redirect('zxdemo_author', releaser_link.releaser_id, permanent=True)


def parties(request):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

	parties_with_spectrum_entries = list(Party.objects.filter(
		competitions__placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).distinct().values_list('id', flat=True))
	parties_with_spectrum_invitations = list(Party.objects.filter(
		invitations__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).distinct().values_list('id', flat=True))

	parties = Party.objects.filter(
		id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations)
	).order_by('start_date_date')
	return render(request, 'zxdemo/parties.html', {
		'parties': parties,
	})


def parties_year(request, year):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

	parties_with_spectrum_entries = list(Party.objects.filter(
		competitions__placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).distinct().values_list('id', flat=True))
	parties_with_spectrum_invitations = list(Party.objects.filter(
		invitations__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).distinct().values_list('id', flat=True))

	parties = Party.objects.filter(
		id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations),
		start_date_date__year=year
	).distinct().order_by('start_date_date')

	all_years = Party.objects.filter(
		id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations),
	).dates('start_date_date', 'year')

	return render(request, 'zxdemo/parties_year.html', {
		'year': int(year),
		'all_years': all_years,
		'parties': parties,
	})


def partycalendar_redirect(request):
	year = request.GET.get('year')
	if year:
		return redirect('zxdemo_parties_year', year, permanent=True)
	else:
		return redirect('zxdemo_parties', permanent=True)


def party(request, party_id):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	party = get_object_or_404(Party, id=party_id)

	# all competitions with at least one Spectrum entry
	competitions = party.competitions.filter(
		placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
	).distinct().order_by('name', 'id')
	competitions_with_placings = []

	for competition in competitions:
		placings = competition.placings.order_by('position', 'production__id').prefetch_related(
			'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser', 'production__platforms', 'production__types'
		).defer('production__notes', 'production__author_nicks__releaser__notes', 'production__author_affiliation_nicks__releaser__notes')

		screenshots = Screenshot.objects.filter(
			production__competition_placings__competition=competition,
			production__platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('?')[:math.ceil(len(placings) / 6.0)]

		competitions_with_placings.append(
			(
				competition, placings, screenshots,
				any([placing.ranking for placing in placings]),
				any([placing.score for placing in placings]),
			)
		)

	# Do not show an invitations section in the special case that all invitations are
	# entries in a competition at this party (which probably means that it was an invitation compo)
	invitations = party.invitations.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')
	non_competing_invitations = invitations.exclude(competition_placings__competition__party=party)
	if not non_competing_invitations:
		invitations = Production.objects.none

	return render(request, 'zxdemo/party.html', {
		'party': party,
		'competitions_with_placings': competitions_with_placings,
		'invitations': invitations,
	})
