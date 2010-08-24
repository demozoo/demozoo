from demoscene.models import Releaser, Nick, NickVariant

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		nicks = Nick.objects.filter(releaser__is_group = True)
		for nick in nicks:
			if nick.abbreviation:
				continue
			for variant in nick.variants.all():
				if variant.name != nick.name and len(variant.name) < 6:
					nick.abbreviation = variant.name
					nick.save()
					break
