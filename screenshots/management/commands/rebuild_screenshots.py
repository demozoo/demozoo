from django.core.management.base import NoArgsCommand
from demoscene.models import Screenshot
from screenshots.tasks import rebuild_screenshot


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		screens = Screenshot.objects.all()
		for screen in screens:
			print "rebuilding %s" % screen
			rebuild_screenshot.delay(screen.id)
