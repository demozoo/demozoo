from django.core.management.base import NoArgsCommand
from mirror.actions import find_zipped_screenshottable_graphics
from screenshots.tasks import create_screenshot_from_production_link


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for prod_link in find_zipped_screenshottable_graphics():
			print "prod %s: download from %s" % (prod_link.production_id, prod_link.download_url)
			create_screenshot_from_production_link.delay(prod_link.id)
