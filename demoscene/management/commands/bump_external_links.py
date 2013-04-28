# Re-parse all external links of type 'BaseUrl' or 'SceneOrgFile', in case
# they're now recognised as a more specific type
from django.core.management.base import NoArgsCommand
from demoscene.models import PartyExternalLink, ReleaserExternalLink, ProductionLink

external_link_models = [PartyExternalLink, ReleaserExternalLink, ProductionLink]


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for model in external_link_models:
			for link in model.objects.filter(link_class__in=['BaseUrl', 'SceneOrgFile']):
				original_link_class = link.link_class
				if link.link_class == 'BaseUrl':
					link.url = link.url
				else:
					link.url = link.link.nl_url
				if link.link_class != original_link_class:
					print "%s ID %s bumped to %s" % (model.__name__, link.id, link.link_class)
					link.save()
