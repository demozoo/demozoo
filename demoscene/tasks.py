from celery.task import task
from demoscene.models import Party
from sceneorg.models import File

@task(rate_limit = '6/m', ignore_result = True)
def add_sceneorg_results_file_to_party(party_id, file_id):
	party = Party.objects.get(id = party_id)
	file = File.objects.get(id = file_id)
	party.add_sceneorg_file_as_results_file(file)

