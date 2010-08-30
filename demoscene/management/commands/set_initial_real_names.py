from demoscene.models import Releaser
import re
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for releaser in Releaser.objects.all():
			if releaser.first_name and releaser.surname:
				continue
			m = re.search(r'real name:\s*(.*?)(\.|\n)', releaser.notes, re.I)
			if m:
				full_name = m.group(1);
				print "%s => %s" % (releaser.name, full_name)

