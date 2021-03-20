from __future__ import absolute_import, unicode_literals

import datetime
import json
import logging
import urllib

from celery import shared_task
from django.conf import settings

from demoscene.models import Releaser, ReleaserExternalLink
from pouet.matching import automatch_productions
from pouet.models import Group, Production


# Get an instance of a logger
logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def pull_groups():
    for link in ReleaserExternalLink.objects.filter(link_class='PouetGroup'):
        pull_group.delay(link.parameter, link.releaser_id)


def fetch_group(group_data, groups_by_id):
    """
    Return a Group record for the given group data, looking up first in groups_by_id,
    then in the database, then creating a database record if not found
    """
    try:
        group_id = int(group_data['id'])
        return groups_by_id[group_id]
    except KeyError:
        group, created = Group.objects.update_or_create(pouet_id=group_id, defaults={
            'name': group_data['name'],
            'last_seen_at': datetime.datetime.now(),
        })
        groups_by_id[group_id] = group
        return group


@shared_task(rate_limit='1/s', ignore_result=True)
def pull_group(pouet_id, releaser_id):
    url = 'https://api.pouet.net/v1/group/?id=%d' % int(pouet_id)
    req = urllib.request.Request(url, None, {'User-Agent': settings.HTTP_USER_AGENT})
    page = urllib.request.urlopen(req)
    response = json.loads(page.read())
    page.close()

    if not response.get('success'):
        logger.warning("pouet.net API request returned non-success! %r" % response)
        return

    logger.info("API request to %s succeeded" % url)

    group_data = response['group']
    group, created = Group.objects.update_or_create(pouet_id=pouet_id, defaults={
        'name': group_data['name'],
        'demozoo_id': group_data['demozoo'],
        'last_seen_at': datetime.datetime.now(),
    })

    groups_by_id = {int(pouet_id): group}

    if 'prods' not in group_data:
        return

    for prod_data in group_data['prods']:
        prod, created = Production.objects.update_or_create(pouet_id=prod_data['id'], defaults={
            'name': prod_data['name'],
            'last_seen_at': datetime.datetime.now(),
        })
        prod.groups.set([fetch_group(g, groups_by_id) for g in prod_data['groups']])

    automatch_productions(Releaser.objects.get(id=releaser_id))


@shared_task(ignore_result=True)
def automatch_all_groups():
    # garbage-collect productions / groups that haven't been seen for 30 days (i.e. have been deleted from Pouet)
    last_month = datetime.datetime.now() - datetime.timedelta(days=30)
    Production.objects.filter(last_seen_at__lt=last_month).delete()
    Group.objects.filter(last_seen_at__lt=last_month).delete()

    for releaser_id in ReleaserExternalLink.objects.filter(link_class='PouetGroup').values_list('releaser_id', flat=True):
        automatch_group.delay(releaser_id)


@shared_task(rate_limit='6/m', ignore_result=True)
def automatch_group(releaser_id):
    automatch_productions(Releaser.objects.get(id=releaser_id))
