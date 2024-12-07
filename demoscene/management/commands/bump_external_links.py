# Re-parse all external links of type 'BaseUrl' or 'SceneOrgFile', in case
# they're now recognised as a more specific type
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from bbs.models import BBSExternalLink
from demoscene.models import ReleaserExternalLink
from parties.models import PartyExternalLink
from productions.models import ProductionLink


external_link_models = [
    (PartyExternalLink, "party_id"),
    (ReleaserExternalLink, "releaser_id"),
    (ProductionLink, "production_id"),
    (BBSExternalLink, "bbs_id"),
]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for model, fk_name in external_link_models:
            for link in model.objects.filter(
                link_class__in=["BaseUrl", "UntergrundFile", "SceneOrgFile", "ZxArtPicture", "ZxArtMusic"]
            ):
                original_link_class = link.link_class
                if link.link_class == "SceneOrgFile":
                    link.url = link.link.nl_url
                else:
                    link.url = link.url
                if link.link_class != original_link_class:
                    item_id = getattr(link, fk_name)
                    print("%s ID %s on item %s bumped to %s" % (model.__name__, link.id, item_id, link.link_class))
                    try:
                        sid = transaction.savepoint()
                        link.save()
                        transaction.savepoint_commit(sid)
                    except IntegrityError:
                        # this link duplicates an existing one - we just didn't recognise it
                        # until now due to different link formats. Fair game to delete it
                        transaction.savepoint_rollback(sid)
                        print("%s ID %s (%s) deleted as dupe" % (model.__name__, link.id, link.url))
                        link.delete()
