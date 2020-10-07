from __future__ import absolute_import, unicode_literals

# Fetch results files from scene.org that are in the db as ResultsFile records
# but missing on the local filesystem

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from parties.models import ResultsFile

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for results_file in ResultsFile.objects.select_related('party'):
            try:
                results_file.data
                print("Found file for %s" % results_file.party.name)
                continue
            except IOError:
                print("Missing file for %s" % results_file.party.name)

            sceneorg_file = results_file.party.sceneorg_results_file()
            if sceneorg_file:
                print(" - Found on scene.org at %s" % sceneorg_file.path)
                results_file.file.save(results_file.party.clean_name + '.txt', ContentFile(sceneorg_file.fetched_data()))
            else:
                print(" - Not found on scene.org")
