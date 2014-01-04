from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from demoscene.models import Production, Screenshot, ProductionLink, Releaser, ReleaserExternalLink, Membership, Credit
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
