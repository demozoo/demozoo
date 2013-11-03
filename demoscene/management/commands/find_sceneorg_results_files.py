from demoscene.tasks import find_sceneorg_results_files

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		def callback(party):
			print "found results.txt for %s" % party

		find_sceneorg_results_files(callback)
