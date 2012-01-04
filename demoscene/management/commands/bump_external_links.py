# Re-parse all external links of type 'BaseUrl', in case they're now recognised as a
# specific type
from django.core.management.base import NoArgsCommand
from demoscene.models import PartyExternalLink, ReleaserExternalLink, ProductionLink

external_link_models = [PartyExternalLink, ReleaserExternalLink, ProductionLink]

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for model in external_link_models:
			for link in model.objects.filter(link_class='BaseUrl'):
				link.url = link.parameter
				if link.link_class != 'BaseUrl':
					link.save()
