from celery import shared_task

from parties.models import Party
from sceneorg.models import File


@shared_task(rate_limit='6/m', ignore_result=True)
def add_sceneorg_results_file_to_party(party_id, file_id):
    party = Party.objects.get(id=party_id)
    file = File.objects.get(id=file_id)
    party.add_sceneorg_file_as_results_file(file)


def find_sceneorg_results_files(callback=None):
    parties = Party.objects.filter(results_files__isnull=True)
    for party in parties:
        file = party.sceneorg_results_file()
        if file:
            add_sceneorg_results_file_to_party.delay(party.id, file.id)
            if callback:
                callback(party)
