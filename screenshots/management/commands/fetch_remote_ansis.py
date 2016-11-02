from django.core.management.base import NoArgsCommand
from mirror.actions import find_ansis
from screenshots.tasks import create_ansi_from_production_link


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for prod_link in find_ansis():
			print "prod %s: download from %s" % (prod_link.production_id, prod_link.download_url)
			create_ansi_from_production_link.delay(prod_link.id)
