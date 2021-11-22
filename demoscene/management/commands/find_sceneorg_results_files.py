from django.core.management.base import BaseCommand

from demoscene.tasks import find_sceneorg_results_files


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        def callback(party):
            print("found results.txt for %s" % party)

        find_sceneorg_results_files(callback)
