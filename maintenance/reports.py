import redis

from django.conf import settings

from productions.models import Production
from maintenance.models import Exclusion


def productions_without_screenshots(limit=100):

	r = redis.StrictRedis.from_url(settings.REDIS_URL)

	if not r.exists('demozoo:productions:without_screenshots'):
		excluded_ids = Exclusion.objects.filter(report_name='prods_without_screenshots').values_list('record_id', flat=True)

		production_ids = (
			Production.objects
			.filter(default_screenshot__isnull=True)
			.filter(links__is_download_link=True)
			.exclude(supertype='music')
			.exclude(id__in=excluded_ids)
		).values_list('id', flat=True)

		if production_ids:
			p = r.pipeline()
			p.delete('demozoo:productions:without_screenshots')
			p.sadd('demozoo:productions:without_screenshots', *production_ids)
			p.expire('demozoo:productions:without_screenshots', 600)
			p.execute()

	production_ids = r.srandmember('demozoo:productions:without_screenshots', number=limit)
	count = r.scard('demozoo:productions:without_screenshots')

	productions = (
		Production.objects.filter(id__in=production_ids)
		.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')
		.defer('notes')
	)

	return (productions, count)
