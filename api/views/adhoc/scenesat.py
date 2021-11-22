import csv

from django.http import HttpResponse

from api.utils import get_month_parameter
from productions.models import Production


def monthly(request):
    # Get a list of music released in the given calendar month
    # (default: the calendar month just gone)

    (start_date, end_date) = get_month_parameter(request)

    prods = Production.objects.filter(
        supertype='music',
        release_date_date__gte=start_date, release_date_date__lt=end_date,
    ).exclude(release_date_precision='y').prefetch_related(
        'types', 'platforms',
        'author_nicks', 'author_affiliation_nicks',
    ).order_by('release_date_date')

    response = HttpResponse(content_type='text/plain;charset=utf-8')
    csvfile = csv.writer(response)
    csvfile.writerow([
        'Demozoo URL', 'Title', 'By', 'Release date', 'Type', 'Platform', 'Download URL'
    ])
    for prod in prods:
        platforms = sorted(prod.platforms.all(), key=lambda p: p.name)
        prod_types = sorted(prod.types.all(), key=lambda t: t.name)
        csvfile.writerow([
            (u'http://demozoo.org' + prod.get_absolute_url()).encode('utf-8'),
            prod.title.encode('utf-8'),
            prod.byline_string.encode('utf-8'),
            prod.release_date,
            ', '.join([typ.name for typ in prod_types]).encode('utf-8'),
            ', '.join([platform.name for platform in platforms]).encode('utf-8'),
            ' / '.join([link.download_url for link in prod.links.all() if link.is_download_link]).encode('utf-8'),
        ])

    return response
