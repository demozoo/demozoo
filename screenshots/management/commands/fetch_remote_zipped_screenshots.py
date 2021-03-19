from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from mirror.actions import find_zipped_screenshottable_graphics
from screenshots.tasks import create_screenshot_from_production_link


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for prod_link in find_zipped_screenshottable_graphics():
            print("prod %s: download from %s" % (prod_link.production_id, prod_link.download_url))
            create_screenshot_from_production_link.delay(prod_link.id)
