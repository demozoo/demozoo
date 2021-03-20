from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from janeway.models import Screenshot as JanewayScreenshot
from janeway.tasks import import_screenshot


class Command(BaseCommand):
    """Import screenshots from Janeway"""
    def handle(self, *args, **kwargs):
        screenshots = JanewayScreenshot.objects.raw("""
            SELECT janeway_screenshot.*, productions_productionlink.production_id
            FROM janeway_screenshot
            LEFT JOIN productions_screenshot ON (
                janeway_screenshot.janeway_id = productions_screenshot.janeway_id
                AND janeway_screenshot.suffix = productions_screenshot.janeway_suffix
            )
            INNER JOIN janeway_release ON (janeway_screenshot.release_id = janeway_release.id)
            INNER JOIN productions_productionlink ON (
                link_class = 'KestraBitworldRelease' and parameter = cast(janeway_release.janeway_id as varchar)
            )
            WHERE productions_screenshot IS NULL
        """)

        for (index, screenshot) in enumerate(screenshots):
            if (index % 100 == 0):
                print("queued %d screenshot fetches" % index)

            import_screenshot.delay(screenshot.production_id, screenshot.janeway_id, screenshot.url, screenshot.suffix)
