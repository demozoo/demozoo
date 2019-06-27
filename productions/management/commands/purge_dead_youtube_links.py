from django.core.management.base import BaseCommand

from productions.models import ProductionLink
from productions.tasks import clean_dead_youtube_link


class Command(BaseCommand):
	def handle(self, *args, **kwargs):
		prod_links = ProductionLink.objects.filter(link_class='YoutubeVideo')

		for prod_link in prod_links:
			print "scheduling fetch for %s" % prod_link.link
			clean_dead_youtube_link.delay(prod_link.id)
