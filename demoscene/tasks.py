from celery.task import task
from django.db import connection, transaction
import random
from itertools import groupby

from parties.models import Party
from sceneorg.models import File

@task(rate_limit = '6/m', ignore_result = True)
def add_sceneorg_results_file_to_party(party_id, file_id):
	party = Party.objects.get(id = party_id)
	file = File.objects.get(id = file_id)
	party.add_sceneorg_file_as_results_file(file)


def find_sceneorg_results_files(callback=None):
	parties = Party.objects.filter(results_files__isnull = True)
	for party in parties:
		file = party.sceneorg_results_file()
		if file:
			add_sceneorg_results_file_to_party.delay(party.id, file.id)
			if callback:
				callback(party)


@task(ignore_result=True)
def set_default_screenshots():
	cur = connection.cursor()
	cur2 = connection.cursor()

	# unset default_screenshot for productions that don't have any processed screenshots
	# (if things are working properly then we would expect this to be redundant. But no harm in being thorough :-) )
	cur.execute('''
		UPDATE productions_production SET default_screenshot_id = NULL
		WHERE id NOT IN (SELECT DISTINCT production_id FROM productions_screenshot WHERE thumbnail_url <> '')
	''')

	# get all processed screenshots (= ones that have thumbnails), group by production_id
	cur.execute("SELECT id, production_id FROM productions_screenshot WHERE thumbnail_url <> '' ORDER BY production_id")
	for production_id, screenshots in groupby(cur, lambda row: row[1]):
		# select a random screenshot from the group and set it as default_screenshot for that prod
		screenshot_id = random.choice([row[0] for row in screenshots])
		cur2.execute('''
			UPDATE productions_production SET default_screenshot_id = %s WHERE id = %s
		''', [screenshot_id, production_id])

	transaction.commit_unless_managed()
