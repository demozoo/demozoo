from demoscene.models import Production
import re
from string import replace
from fuzzy_date import FuzzyDate
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for prod in Production.objects.all():
			if prod.release_date:
				continue
			note_match = re.search(r'release date:\s*(.*?)[\.\s]*(\n|$)', prod.notes, re.I)
			if note_match:
				date = FuzzyDate.parse(note_match.group(1))
				print "%s: %s" % (prod.title, date)
				# prod.release_date = date
				# prod.notes = replace(prod.notes, note_match.group(0), '')
				# prod.save()
