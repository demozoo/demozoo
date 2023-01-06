import datetime
import gzip
import json
import time

import requests
from django.core.management.base import BaseCommand

from demoscene.models import Releaser
from pouet.matching import automatch_productions, get_pouetable_prod_types
from pouet.models import CompetitionPlacing, CompetitionType, Group, GroupMatchInfo, Party, Platform, Production, ProductionType


class Command(BaseCommand):
    help = "Import latest Pouet data dump from data.pouet.net"

    def handle(self, *args, **kwargs):
        verbose = kwargs['verbosity'] >= 1

        # Dumps are published every Wednesday morning, so find out when last Wednesday was
        today = datetime.date.today()
        days_since_wednesday = (today.weekday() - 2) % 7
        wednesday = today - datetime.timedelta(days=days_since_wednesday)
        datestamp = wednesday.strftime('%Y%m%d')
        monthstamp = wednesday.strftime('%Y%m')

        if verbose:
            print("importing groups...")
        groups_url = "https://data.pouet.net/dumps/%s/pouetdatadump-groups-%s.json.gz" % (monthstamp, datestamp)
        r = requests.get(groups_url, stream=True)
        groups_file = gzip.GzipFile(fileobj=r.raw)

        groups_imported = 0
        groups_created = 0

        group_db_ids = {}

        def handle_group(group_data):
            nonlocal groups_imported, groups_created
            if 'id' in group_data:
                group, created = Group.objects.update_or_create(pouet_id=group_data['id'], defaults={
                    'name': group_data['name'],
                    'demozoo_id': group_data['demozoo'],
                    'last_seen_at': datetime.datetime.now(),
                })
                group_db_ids[group_data['id']] = group.id
                groups_imported += 1
                if groups_imported % 1000 == 0 and verbose:  # pragma: no cover
                    print("%d groups imported" % groups_imported)

                if created:
                    groups_created += 1

        json.load(groups_file, object_hook=handle_group)
        groups_file.close()
        if verbose:
            print("done. %d groups imported, of which %d newly created" % (groups_imported, groups_created))

        if verbose:
            print("importing prods...")
        prods_url = "https://data.pouet.net/dumps/%s/pouetdatadump-prods-%s.json.gz" % (monthstamp, datestamp)
        r = requests.get(prods_url, stream=True)
        prods_file = gzip.GzipFile(fileobj=r.raw)

        prods_imported = 0
        prods_created = 0

        platforms_by_id = {}
        prod_types_by_name = {}
        parties_by_id = {}
        competition_types_by_id = {}

        def handle_prod(prod_data):
            nonlocal prods_imported, prods_created, group_db_ids
            # prods JSON contains various nested objects, but only prod entries have a 'download' field
            if 'download' in prod_data:
                prod, prod_created = Production.objects.update_or_create(pouet_id=prod_data['id'], defaults={
                    'name': prod_data['name'],
                    'download_url': prod_data['download'],
                    'vote_up_count': prod_data['voteup'],
                    'vote_pig_count': prod_data['votepig'],
                    'vote_down_count': prod_data['votedown'],
                    'cdc_count': prod_data['cdc'],
                    'popularity': prod_data['popularity'],
                    'last_seen_at': datetime.datetime.now(),
                })
                prod.groups.set([
                    group_db_ids[group['id']]
                    for group in prod_data['groups']
                ])
                if prod_created:
                    unseen_download_link_ids = set()
                    unseen_placings = set()
                else:
                    unseen_download_link_ids = set(prod.download_links.values_list('id', flat=True))
                    unseen_placings = {
                        (placing.party_id, placing.year, placing.competition_type_id, placing.ranking): placing.id
                        for placing in prod.competition_placings.all()
                    }

                for link_data in prod_data['downloadLinks']:
                    link, created = prod.download_links.get_or_create(
                        url=link_data['link'], link_type=link_data['type']
                    )
                    if not created:
                        unseen_download_link_ids.discard(link.id)

                if unseen_download_link_ids:
                    prod.download_links.filter(id__in=unseen_download_link_ids).delete()

                platform_ids = []
                for (platform_id, platform_data) in prod_data['platforms'].items():
                    try:
                        platform = platforms_by_id[platform_id]
                    except KeyError:
                        platform, created = Platform.objects.get_or_create(pouet_id=platform_id, defaults={
                            'name': platform_data['name']
                        })
                        platforms_by_id[platform_id] = platform
                    platform_ids.append(platform.id)
                prod.platforms.set(platform_ids)

                prod_type_ids = []
                for type_name in prod_data['types']:
                    try:
                        prod_type = prod_types_by_name[type_name]
                    except KeyError:
                        prod_type, created = ProductionType.objects.get_or_create(name=type_name)
                        prod_types_by_name[type_name] = prod_type
                    prod_type_ids.append(prod_type.id)
                prod.types.set(prod_type_ids)

                for placing_data in prod_data['placings']:
                    if placing_data['year'] is None:
                        # bad data
                        continue

                    party_data = placing_data['party']
                    try:
                        party = parties_by_id[party_data['id']]
                    except KeyError:
                        party, created = Party.objects.get_or_create(pouet_id=party_data['id'], defaults={
                            'name': party_data['name']
                        })
                        parties_by_id[party_data['id']] = party

                    if placing_data['compo'] is None:
                        compo_type_id = None
                    else:
                        try:
                            compo_type = competition_types_by_id[placing_data['compo']]
                        except KeyError:
                            compo_type, created = CompetitionType.objects.get_or_create(
                                pouet_id=placing_data['compo'],
                                defaults={
                                    'name': placing_data['compo_name']
                                }
                            )
                            competition_types_by_id[placing_data['compo']] = compo_type
                        compo_type_id = compo_type.id

                    placing, created = prod.competition_placings.get_or_create(
                        party=party, year=placing_data['year'], competition_type_id=compo_type_id, ranking=placing_data['ranking']
                    )
                    if not created:
                        try:
                            ranking = int(placing_data['ranking'])
                        except TypeError:
                            ranking = None
                        record = (party.id, int(placing_data['year']), compo_type_id, ranking)
                        del unseen_placings[record]
                    if unseen_placings:
                        prod.competition_placings.filter(id__in=unseen_placings.values()).delete()

                prods_imported += 1
                if prods_imported % 1000 == 0 and verbose:  # pragma: no cover
                    print("%d prods imported" % prods_imported)

                if prod_created:
                    prods_created += 1

            return prod_data

        json.load(prods_file, object_hook=handle_prod)
        prods_file.close()
        if verbose:
            print("done. %d prods imported, of which %d newly created" % (prods_imported, prods_created))

        # garbage-collect productions / groups that haven't been seen for 30 days (i.e. have been deleted from Pouet)
        last_month = datetime.datetime.now() - datetime.timedelta(days=30)
        Production.objects.filter(last_seen_at__lt=last_month).delete()
        Group.objects.filter(last_seen_at__lt=last_month).delete()

        # garbage-collect GroupMatchInfo stats for releasers with no corresponding Pouet cross-link
        GroupMatchInfo.objects.exclude(releaser__external_links__link_class='PouetGroup').delete()

        if verbose:
            print("automatching prods...")
        pouetable_prod_types = get_pouetable_prod_types()
        for i, releaser in enumerate(Releaser.objects.filter(external_links__link_class='PouetGroup').only('id')):
            automatch_productions(releaser, pouetable_prod_types=pouetable_prod_types)
            if i % 10 == 0 and i != 0:  # pragma: no cover
                if verbose:
                    print("%d releasers automatched" % i)
                time.sleep(2)
