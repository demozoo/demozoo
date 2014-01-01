from django.shortcuts import render
from django.conf import settings
from django.db import connection

from demoscene.models import Production, Screenshot
from zxdemo.models import NewsItem

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

	news_items = NewsItem.objects.order_by('-created_at').select_related('created_by_user')[:8]

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
