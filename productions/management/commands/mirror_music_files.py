import time
import urllib
from os.path import splitext
from socket import timeout

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.text import slugify

from mirror.actions import FileTooBig, fetch_origin_url
from productions.cowbell import get_playable_track_data
from productions.models import ProductionLink
from screenshots.processing import upload_to_s3


class Command(BaseCommand):
    """Find remote music files suitable for mirroring on media.demozoo.org (so we can play them with cowbell)"""
    def handle(self, *args, **kwargs):
        filetype_filter = (
            Q(parameter__iendswith='.sap') | Q(parameter__iendswith='.sid')
            | Q(parameter__iendswith='.sndh')
            | Q(parameter__iendswith='.mod') | Q(parameter__iendswith='.s3m')
            | Q(parameter__iendswith='.xm') | Q(parameter__iendswith='.it')
        )
        links = ProductionLink.objects.filter(
            is_download_link=True,
            link_class__in=[
                'BaseUrl', 'AmigascneFile', 'SceneOrgFile', 'FujiologyFile', 'UntergrundFile', 'PaduaOrgFile'
            ],
            production__supertype='music',
        ).filter(
            filetype_filter
        ).exclude(
            parameter__istartswith='https://media.demozoo.org/'
        ).select_related('production')

        for prod_link in links:
            # see if this prod already has a playable link
            tracks, media = get_playable_track_data(prod_link.production)
            if tracks:
                # already playable
                continue

            print("prod %s: downloading from %s" % (prod_link.production_id, prod_link.url))
            try:
                download = fetch_origin_url(prod_link.download_url)
                sha1 = download.sha1
                (basename, file_ext) = splitext(download.filename)

                filename = 'music/' + sha1[0:2] + '/' + sha1[2:4] + '/' + slugify(basename) + file_ext
                new_url = upload_to_s3(download.as_io_buffer(), filename)
                ProductionLink.objects.create(
                    production=prod_link.production,
                    link_class='BaseUrl', parameter=new_url,
                    is_download_link=True
                )
            except (urllib.error.URLError, FileTooBig, timeout):
                pass

            time.sleep(1)
