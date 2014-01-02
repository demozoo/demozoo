from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from demoscene.models import Releaser

class NewsItem(models.Model):
	title = models.CharField(max_length=255, blank=True)
	body = models.TextField()
	created_at = models.DateTimeField()
	author = models.ForeignKey(User)

	def __unicode__(self):
		return self.title


def filter_releasers_queryset_to_spectrum(queryset, releaser_table='demoscene_releaser'):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	return queryset.extra(
		where=[
			"""
			%(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_production_author_nicks ON (demoscene_production_platforms.production_id = demoscene_production_author_nicks.production_id)
				INNER JOIN demoscene_nick ON (demoscene_production_author_nicks.nick_id = demoscene_nick.id)
				WHERE demoscene_production_platforms.platform_id IN (%%s)
			)
			OR %(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production_platforms.production_id = demoscene_production_author_affiliation_nicks.production_id)
				INNER JOIN demoscene_nick ON (demoscene_production_author_affiliation_nicks.nick_id = demoscene_nick.id)
				WHERE demoscene_production_platforms.platform_id IN (%%s)
			)
			OR %(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM demoscene_production_platforms
				INNER JOIN demoscene_credit ON (demoscene_production_platforms.production_id = demoscene_credit.production_id)
				INNER JOIN demoscene_nick ON (demoscene_credit.nick_id = demoscene_nick.id)
				WHERE demoscene_production_platforms.platform_id IN (%%s)
			)
			""" % {'releaser_table': releaser_table}
		],
		params=[tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS)]
	)

def spectrum_releasers():
	return filter_releasers_queryset_to_spectrum(Releaser.objects.all())
