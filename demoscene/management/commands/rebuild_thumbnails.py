from django.core.management.base import NoArgsCommand
from demoscene.models import Screenshot
from model_thumbnail import generate_thumbnail

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		screens = Screenshot.objects.all()
		for screen in screens:
			print "rebuilding %s" % screen
			try:
				generate_thumbnail(screen.original, screen.thumbnail, (135, 90), crop = True)
				screen.save()
			except AttributeError: # thrown on broken image link
				pass
