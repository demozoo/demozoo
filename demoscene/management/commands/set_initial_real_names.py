from demoscene.models import Releaser
import re
from string import rstrip, replace
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for releaser in Releaser.objects.all():
			if releaser.first_name and releaser.surname:
				continue
			note_match = re.search(r'real name:\s*(.*?)\s*(\n|\,|\(|$)', releaser.notes, re.I)
			if note_match:
				full_name = note_match.group(1)
				name_match = re.match(r'(.+) (van|von) (.*[^\.])', full_name, re.I)
				if name_match:
					first_name = name_match.group(1)
					surname = ' '.join(name_match.group(2,3))
				else:
					name_match = re.match(r'(.+) (\S*[^\.])', full_name)
					if name_match:
						first_name = name_match.group(1)
						surname = name_match.group(2)
					else:
						first_name = rstrip(full_name, '.')
						surname = ''
				print "%s => [%s] [%s]" % (releaser.name, first_name, surname)
				if first_name != 'n/a':
					releaser.first_name = first_name
					releaser.surname = surname
					releaser.notes = replace(releaser.notes, note_match.group(0), note_match.group(2))
					releaser.save()
