# Re-parse all external links of type 'BaseUrl' or 'SceneOrgFile', in case
# they're now recognised as a more specific type
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.db import transaction
from demoscene.models import ReleaserExternalLink
from productions.models import ProductionLink
from parties.models import PartyExternalLink

external_link_models = [PartyExternalLink, ReleaserExternalLink, ProductionLink]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for model in external_link_models:
            for link in model.objects.filter(link_class__in=['BaseUrl', 'UntergrundFile', 'SceneOrgFile']):
                original_link_class = link.link_class
                if link.link_class == 'SceneOrgFile':
                    link.url = link.link.nl_url
                else:
                    link.url = link.url
                if link.link_class != original_link_class:
                    print "%s ID %s bumped to %s" % (model.__name__, link.id, link.link_class)
                    try:
                        sid = transaction.savepoint()
                        link.save()
                        transaction.savepoint_commit(sid)
                    except IntegrityError:
                        # this link duplicates an existing one - we just didn't recognise it
                        # until now due to different link formats. Fair game to delete it
                        transaction.savepoint_rollback(sid)
                        print "%s ID %s (%s) deleted as dupe" % (model.__name__, link.id, link.url)
                        link.delete()
