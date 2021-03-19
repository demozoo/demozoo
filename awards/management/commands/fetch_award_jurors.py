from __future__ import absolute_import, unicode_literals

import re

import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from awards.models import Event, Juror
from demoscene.models import SceneID


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        events = Event.objects.filter(reporting_enabled=True).exclude(juror_feed_url='')
        for event in events:
            sceneids = []

            try:
                r = requests.get(event.juror_feed_url)
            except requests.RequestException as e:
                print("Error while fetching juror feed URL for %s: %s" % (event.name, e))
                continue

            for line in r.iter_lines():
                # it's probably utf-8, but we only care about the number at the start
                # so decode as iso-8859-1 for extra fault-tolerance
                line = line.decode('iso-8859-1')

                match = re.match(r'^(\d+)\s*(?:\#.*)?$', line)
                if match:
                    sceneids.append(int(match.group(1)))

            # add Juror records for user accounts matching these sceneids
            users = User.objects.filter(sceneid__sceneid__in=sceneids)
            for user in users:
                Juror.objects.get_or_create(user=user, event=event)

            # remove non-sticky Juror records for users not in this list
            Juror.objects.filter(event=event, is_sticky=False).exclude(user__in=users).delete()
