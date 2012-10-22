from demoscene.models import Party
from demoscene.tasks import add_sceneorg_results_file_to_party

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		parties = Party.objects.filter(results_files__isnull = True)
		for party in parties:
			file = party.sceneorg_results_file()
			if file:
				add_sceneorg_results_file_to_party.delay(party.id, file.id)
				print "found results.txt for %s" % party
