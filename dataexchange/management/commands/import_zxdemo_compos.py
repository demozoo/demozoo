from django.core.management.base import NoArgsCommand
from parties.models import Party, Competition, CompetitionPlacing
from demoscene.models import Production

import pymysql
import re
from itertools import groupby

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		connection = pymysql.connect(user="root", db="zxdemo")
		cur = connection.cursor()
		cur.execute("SELECT id, party_id, name FROM compo ORDER BY party_id")
		for party_id, compos in groupby(cur, lambda row: row[1]):
			party = Party.objects.get(zxdemo_party_id = party_id)
			if party.competitions.all():
				print "%s already has competitions - skipping" % party
			else:
				for compo_id, _, compo_name in compos:
					compo_name = re.sub(r'\s+[Cc]ompetition\s*', ' ', compo_name).rstrip()
					compo = Competition.objects.create(party = party, name = compo_name)
					print compo
					cur2 = connection.cursor()
					cur2.execute("""
						SELECT item_id, placing, score
						FROM result
						INNER JOIN item ON (result.item_id = item.id AND is_spectrum = 1)
						WHERE compo_id = %s
						ORDER BY sortorder
					""", [compo_id])
					for i, (item_id, placing, score) in enumerate(cur2):
						if item_id == 6081:
							# patch for duplicate of Hellboy by Dron/K3L which was never noticed on zxdemo but was caught by import deduping...
							item_id = 3769
						
						try:
							production = Production.objects.get(zxdemo_id = item_id)
						except Production.DoesNotExist:
							raise Exception("no prod with zxdemo id %d" % item_id)
						result = CompetitionPlacing.objects.create(
							competition = compo,
							production = production,
							ranking = placing,
							score = score,
							position = i+1)
