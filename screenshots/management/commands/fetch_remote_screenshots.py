from django.core.management.base import NoArgsCommand
from mirror.actions import find_screenshottable_graphics
from screenshots.tasks import create_screenshot_from_remote_file


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for url, production_id in find_screenshottable_graphics():
			print url
			create_screenshot_from_remote_file.delay(url, production_id)
