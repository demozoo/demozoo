from django.core.management.base import NoArgsCommand

import datetime

from demoscene.utils.groklinks import EMBEDDABLE_PRODUCTION_LINK_TYPES

from productions.models import ProductionLink
from productions.tasks import fetch_production_link_embed_data


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		link_types = [cls.__name__ for cls in EMBEDDABLE_PRODUCTION_LINK_TYPES]
		last_month = datetime.date.today() - datetime.timedelta(days=30)

		# order by embed_data_last_fetch_time desc to fetch null ones (never fetched) first
		prod_links = ProductionLink.objects.filter(
			link_class__in=link_types
		).exclude(
			embed_data_last_fetch_time__gt=last_month
		).exclude(
			embed_data_last_error_time__gt=last_month
		).order_by('-embed_data_last_fetch_time')

		for prod_link in prod_links:
			print "fetching embed data for %s" % prod_link.link
			fetch_production_link_embed_data.delay(prod_link.id)
