from sceneorg.models import *
from sceneorg.tasks import fetch_sceneorg_file

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		file_ids = File.objects.extra(where=["path LIKE '/parties/%%.txt'"]).values_list('id', flat=True)
		for id in file_ids:
			fetch_sceneorg_file.delay(id)
