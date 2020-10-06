from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from demoscene.models import Releaser
from janeway import matching


class Command(BaseCommand):
    """Find cross-links between Janeway and Demozoo prods identified by title and releaser ID"""
    def handle(self, *args, **kwargs):
        authors = Releaser.objects.filter(external_links__link_class='KestraBitworldAuthor').distinct()

        for (index, author) in enumerate(authors):
            if (index % 100 == 0):
                print("processed %d authors" % index)

            matching.automatch_productions(author)
