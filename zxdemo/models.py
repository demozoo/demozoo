from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from demoscene.models import Releaser

class NewsItem(models.Model):
	title = models.CharField(max_length=255, blank=True)
	body = models.TextField()
	created_at = models.DateTimeField()
	author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

	def __unicode__(self):
		return self.title

class Article(models.Model):
	zxdemo_id = models.IntegerField()
	created_at = models.DateTimeField()
	title = models.CharField(max_length=255)
	summary = models.TextField()
	content = models.TextField()

	def __unicode__(self):
		return self.title


def filter_releasers_queryset_to_spectrum(queryset, releaser_table='demoscene_releaser'):
	ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
	return queryset.extra(
		where=[
			"""
			%(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM productions_production_platforms
				INNER JOIN productions_production_author_nicks ON (productions_production_platforms.production_id = productions_production_author_nicks.production_id)
				INNER JOIN demoscene_nick ON (productions_production_author_nicks.nick_id = demoscene_nick.id)
				WHERE productions_production_platforms.platform_id IN (%%s)
			)
			OR %(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM productions_production_platforms
				INNER JOIN productions_production_author_affiliation_nicks ON (productions_production_platforms.production_id = productions_production_author_affiliation_nicks.production_id)
				INNER JOIN demoscene_nick ON (productions_production_author_affiliation_nicks.nick_id = demoscene_nick.id)
				WHERE productions_production_platforms.platform_id IN (%%s)
			)
			OR %(releaser_table)s.id IN (
				SELECT DISTINCT demoscene_nick.releaser_id
				FROM productions_production_platforms
				INNER JOIN productions_credit ON (productions_production_platforms.production_id = productions_credit.production_id)
				INNER JOIN demoscene_nick ON (productions_credit.nick_id = demoscene_nick.id)
				WHERE productions_production_platforms.platform_id IN (%%s)
			)
			""" % {'releaser_table': releaser_table}
		],
		params=[tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS)]
	)

def spectrum_releasers():
	return filter_releasers_queryset_to_spectrum(Releaser.objects.all())
