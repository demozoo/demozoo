from django.core.management.base import BaseCommand
from django.db import transaction

from bbs.models import BBS
from demoscene.models import Releaser
from parties.models import Party
from productions.models import Production
from search.indexing import index


class Command(BaseCommand):
    help = "Re-indexes all searchable models"

    def handle(self, *args, **kwargs):
        BATCH_SIZE = 1000

        for klass, qs in [
            (BBS, BBS.objects.order_by('pk').defer('search_document')),
            (Party, Party.objects.order_by('pk').defer('search_document')),
            (Releaser, Releaser.objects.order_by('pk').prefetch_related('nicks__variants').defer('search_document')),
            (Production, Production.objects.order_by('pk').prefetch_related('tags').defer('search_document'))
        ]:
            i = 0
            while True:
                with transaction.atomic():
                    batch = qs[i:(i + BATCH_SIZE)]

                    for obj in batch:
                        index(obj)
                        i += 1
                        if i % 100 == 0:  # pragma: no cover
                            print(klass, i)

                if len(batch) < BATCH_SIZE:
                    break
