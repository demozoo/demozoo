import datetime
import gzip
import json

import requests
from django.core.management.base import BaseCommand

from pouet.models import Group


class Command(BaseCommand):
    help = "Import latest Pouet data dump from data.pouet.net"

    def handle(self, *args, **kwargs):
        # Dumps are published every Wednesday morning, so find out when last Wednesday was
        today = datetime.date.today()
        days_since_wednesday = (today.weekday() - 2) % 7
        wednesday = today - datetime.timedelta(days=days_since_wednesday)
        datestamp = wednesday.strftime('%Y%m%d')

        groups_url = "https://data.pouet.net/dumps/202111/pouetdatadump-groups-%s.json.gz" % datestamp
        r = requests.get(groups_url, stream=True)
        groups_file = gzip.GzipFile(fileobj=r.raw)

        groups_imported = 0
        groups_created = 0

        def handle_group(group_data):
            nonlocal groups_imported, groups_created
            if 'id' in group_data:
                group, created = Group.objects.update_or_create(pouet_id=group_data['id'], defaults={
                    'name': group_data['name'],
                    'demozoo_id': group_data['demozoo'],
                    'last_seen_at': datetime.datetime.now(),
                })
                groups_imported += 1
                if groups_imported % 1000 == 0:
                    print("%d groups imported" % groups_imported)

                if created:
                    groups_created += 1

        json.load(groups_file, object_hook=handle_group)
        groups_file.close()
        print("done: %d groups imported, of which %d newly created" % (groups_imported, groups_created))
