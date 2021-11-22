from django.core.management.base import BaseCommand

from demoscene.utils.groklinks import EMBEDDABLE_PRODUCTION_LINK_TYPES
from productions.models import ProductionLink
from productions.tasks import fetch_production_link_embed_data


class Command(BaseCommand):
    """
    fetch all embed data that hasn't been fetched at all yet
    """
    def handle(self, *args, **kwargs):
        link_types = [cls.__name__ for cls in EMBEDDABLE_PRODUCTION_LINK_TYPES]

        # order by embed_data_last_fetch_time desc to fetch null ones (never fetched) first
        prod_links = ProductionLink.objects.filter(
            link_class__in=link_types
        ).filter(
            embed_data_last_fetch_time__isnull=True
        )

        for prod_link in prod_links:
            print("fetching embed data for %s" % prod_link.link)
            fetch_production_link_embed_data.delay(prod_link.id)
