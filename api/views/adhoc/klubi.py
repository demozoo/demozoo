from __future__ import absolute_import, unicode_literals

import csv

from django.http import HttpResponse

from api.utils import get_month_parameter
from productions.models import Production


def demoshow(request):
    # Get a list of prods released in the given calendar month
    # (default: the calendar month just gone)
    # that are of supertype production (= not music or gfx)
    # and not only of type diskmag or tool

    (start_date, end_date) = get_month_parameter(request)

    prods = Production.objects.filter(
        supertype='production',
        release_date_date__gte=start_date, release_date_date__lt=end_date,
    ).exclude(release_date_precision='y').prefetch_related(
        'types', 'platforms',
        'author_nicks', 'author_affiliation_nicks', 'links',
        'competition_placings__competition__party', 'release_parties',
    ).order_by('release_date_date')

    # put videos (wilds) into a separate list after the main one
    exe_prods = []

    for prod in prods:
        if prod.types.count() == 0:
            # don't know what type it is, so include it to be on the safe side
            exe_prods.append(prod)
            continue

        # strip out types that are not really suitable for a demo show
        interesting_types = [typ for typ in prod.types.all() if typ.name not in ('Diskmagazine', 'Tool', 'Game', 'Video', 'Pack', 'Musicdisk', 'Chip Music Pack')]

        if len(interesting_types) == 0:
            continue

        exe_prods.append(prod)

    response = HttpResponse(content_type='text/plain;charset=utf-8')
    csvfile = csv.writer(response)
    csvfile.writerow([
        'Demozoo URL', 'Title', 'By', 'Release date', 'Party', 'Type', 'Platform', 'Download URL', 'Video URL', 'Pouet URL'
    ])
    for prod in exe_prods:
        platforms = sorted(prod.platforms.all(), key=lambda p: p.name)
        prod_types = sorted(prod.types.all(), key=lambda t: t.name)
        csvfile.writerow([
            (u'http://demozoo.org' + prod.get_absolute_url()).encode('utf-8'),
            prod.title.encode('utf-8'),
            prod.byline_string.encode('utf-8'),
            prod.release_date,
            ', '.join([placing.competition.party.name for placing in prod.competition_placings.all()] + [party.name for party in prod.release_parties.all()]).encode('utf-8'),
            ', '.join([typ.name for typ in prod_types]).encode('utf-8'),
            ', '.join([platform.name for platform in platforms]).encode('utf-8'),
            ' / '.join([link.download_url for link in prod.links.all() if link.is_download_link]),
            ' / '.join([link.url for link in prod.links.all() if link.is_streaming_video]),
            ' / '.join([link.url for link in prod.links.all() if link.link_class == 'PouetProduction']),
        ])

    return response
