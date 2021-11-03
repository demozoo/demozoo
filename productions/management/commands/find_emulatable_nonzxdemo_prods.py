from __future__ import absolute_import, unicode_literals

from os.path import splitext
from socket import timeout
from time import sleep
from urllib.error import URLError
from urllib.parse import urlparse
from zipfile import BadZipFile

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from mirror.actions import FileTooBig, fetch_link
from productions.models import EmulatorConfig, Production, ProductionLink
from screenshots.processing import upload_to_s3


class Command(BaseCommand):
    """
    Find Spectrum productions that don't have emulator configs or zxdemo download links,
    and see if they have non-zxdemo download links that we can mirror and use to populate
    EmulatorConfig metadata
    (i.e. zip files containing a single tap/tzx/z80/sna/szx file)
    """
    def handle(self, *args, **kwargs):
        prods = Production.objects.filter(
            platforms__name='ZX Spectrum', supertype='production'
        ).exclude(
            id__in=EmulatorConfig.objects.values_list('production_id', flat=True)
        ).exclude(
            id__in=ProductionLink.objects.filter(
                link_class='BaseUrl', parameter__startswith='https://files.zxdemo.org/'
            ).values_list('production_id', flat=True)
        ).prefetch_related('links')

        for prod in prods:
            success = False

            for prod_link in prod.links.all():
                if not prod_link.is_download_link:
                    continue

                url = urlparse(prod_link.download_url)
                basename, ext = splitext(url.path)
                ext = ext.lower()
                if ext in ('.sna', '.tzx', '.tap', '.z80', '.szx'):
                    # yay, we can use this directly
                    print("direct link for %s: %s" % (prod.title, prod_link.download_url))
                    try:
                        download = fetch_link(prod_link)
                    except (URLError, FileTooBig, timeout, BadZipFile):
                        print("- broken link :-(")
                    else:
                        sha1 = download.sha1
                        basename, file_ext = splitext(download.filename)
                        filename = 'emulation/' + sha1[0:2] + '/' + sha1[2:4] + '/' + slugify(basename) + file_ext
                        new_url = upload_to_s3(download.as_io_buffer(), filename)
                        EmulatorConfig.objects.create(
                            production_id=prod.id,
                            launch_url=new_url,
                            emulator='jsspeccy',
                            configuration='{}'
                        )
                        print("- successfully mirrored at %s" % new_url)
                        success = True
                    sleep(1)
                elif ext == '.zip':
                    print("zip file for %s: %s" % (prod.title, prod_link.download_url))
                    try:
                        download = fetch_link(prod_link)
                    except (URLError, FileTooBig, timeout, BadZipFile):
                        print("- broken link :-(")
                    else:
                        try:
                            zip = download.as_zipfile()
                        except BadZipFile:  # pragma: no cover
                            print("- bad zip :-(")
                        else:
                            loadable_file_count = 0
                            for filename in zip.namelist():
                                if filename.startswith('__MACOSX'):
                                    continue
                                ext = filename.split('.')[-1].lower()
                                if ext in ('tap', 'tzx', 'sna', 'z80', 'szx'):
                                    loadable_file_count += 1
                            if loadable_file_count == 1:
                                sha1 = download.sha1
                                basename, file_ext = splitext(download.filename)
                                filename = (
                                    'emulation/' + sha1[0:2] + '/' + sha1[2:4] + '/' +
                                    slugify(basename) + file_ext
                                )
                                new_url = upload_to_s3(download.as_io_buffer(), filename)
                                EmulatorConfig.objects.create(
                                    production_id=prod.id,
                                    launch_url=new_url,
                                    emulator='jsspeccy',
                                    configuration='{}'
                                )
                                print("- successfully mirrored at %s" % new_url)
                                success = True
                            elif loadable_file_count == 0:
                                print("- no loadable files :-(")
                            else:
                                print("- multiple loadable files :-/")
                    sleep(1)

                if success:
                    break
