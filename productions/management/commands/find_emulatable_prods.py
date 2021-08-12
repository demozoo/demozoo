from __future__ import absolute_import, unicode_literals

from io import BytesIO
from zipfile import BadZipFile, ZipFile

from django.core.management.base import BaseCommand
import requests

from productions.models import EmulatorConfig, ProductionLink


class Command(BaseCommand):
    """
    Populate EmulatorConfig metadata from files.zxdemo.org download links;
    find zipfiles containing a single tap/tzx/z80/sna/szx file
    """
    def handle(self, *args, **kwargs):
        prod_links = ProductionLink.objects.filter(
            production__platforms__name='ZX Spectrum',
            link_class='BaseUrl',
            parameter__startswith='https://files.zxdemo.org/',
        )

        for prod_link in prod_links:
            ext = prod_link.parameter.split('.')[-1].lower()
            if ext != 'zip':
                continue
            
            if EmulatorConfig.objects.filter(launch_url=prod_link.parameter).exists():
                continue

            try:
                r = requests.get(prod_link.parameter)
            except requests.exceptions.RequestException:
                continue

            try:
                zip = ZipFile(BytesIO(r.content))
            except BadZipFile:
                continue

            loadable_file_count = 0
            for filename in zip.namelist():
                if filename.startswith('__MACOSX'):
                    continue
                ext = filename.split('.')[-1].lower()
                if ext in ('tap', 'tzx', 'sna', 'z80', 'szx'):
                    loadable_file_count += 1
            if loadable_file_count == 1:
                print("adding emu config for %s" % prod_link.parameter)
                EmulatorConfig.objects.create(
                    production_id=prod_link.production_id,
                    launch_url=prod_link.parameter,
                    emulator='jsspeccy',
                    configuration='{}'
                )
