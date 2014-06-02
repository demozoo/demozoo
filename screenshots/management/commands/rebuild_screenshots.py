from django.core.management.base import NoArgsCommand
from productions.models import Screenshot
from screenshots.tasks import rebuild_screenshot

# Recreate and re-upload files for screenshots that are still in the original format/location,
# as indicated by having URLs under media.demozoo.org/screenshots/ (not /screens/)


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		screens = Screenshot.objects.filter(original_url__contains='/screenshots/')
		for screen in screens:
			print "rebuilding %s" % screen
			rebuild_screenshot.delay(screen.id)
