import csv

from django.contrib.humanize.templatetags.humanize import ordinal
from django.db.models import Q
from django.http import HttpResponse

from pouet.models import Production as PouetProduction
from productions.models import Production, ProductionType


def write_row(csvfile, dz_prod, pouet_prod):
    if pouet_prod:
        vote_diff = pouet_prod.vote_up_count - pouet_prod.vote_down_count
        vote_count = pouet_prod.vote_up_count + pouet_prod.vote_pig_count + pouet_prod.vote_down_count
        vote_avg = vote_diff / vote_count if vote_count else 0

    if dz_prod and pouet_prod:
        csvfile.writerow([
            'https://pouet.net/prod.php?which=%d' % pouet_prod.pouet_id,
            'https://demozoo.org' + dz_prod.get_absolute_url(),
            dz_prod.title,
            dz_prod.byline_string,
            pouet_prod.vote_up_count,
            pouet_prod.vote_pig_count,
            pouet_prod.vote_down_count,
            vote_diff,
            '{:.2f}'.format(vote_avg),
            pouet_prod.cdc_count,
            round(pouet_prod.popularity),
            '; '.join(
                "%s at %s %s" % (ordinal(placing.ranking), placing.competition.party.name, placing.competition.name)
                for placing in dz_prod.competition_placings.all()
            ),
            ', '.join([typ.name for typ in dz_prod.types.all()]),
            ', '.join([platform.name for platform in dz_prod.platforms.all()]),
        ])
    elif dz_prod:
        csvfile.writerow([
            '',
            'https://demozoo.org' + dz_prod.get_absolute_url(),
            dz_prod.title,
            dz_prod.byline_string,
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '; '.join(
                "%s at %s %s" % (ordinal(placing.ranking), placing.competition.party.name, placing.competition.name)
                for placing in dz_prod.competition_placings.all()
            ),
            ', '.join([typ.name for typ in dz_prod.types.all()]),
            ', '.join([platform.name for platform in dz_prod.platforms.all()]),
        ])
    else:
        csvfile.writerow([
            'https://pouet.net/prod.php?which=%d' % pouet_prod.pouet_id,
            '',
            pouet_prod.name,
            ' :: '.join([group.name for group in pouet_prod.groups.all()]),
            pouet_prod.vote_up_count,
            pouet_prod.vote_pig_count,
            pouet_prod.vote_down_count,
            vote_diff,
            '{:.2f}'.format(vote_avg),
            pouet_prod.cdc_count,
            round(pouet_prod.popularity),
            '; '.join(
                (
                    "%s at %s %s" % (ordinal(placing.ranking), placing.party.name, placing.competition_type.name)
                    if placing.competition_type
                    else "%s at %s" % (ordinal(placing.ranking), placing.party.name)
                )
                for placing in pouet_prod.competition_placings.all()
            ),
            ', '.join([typ.name for typ in pouet_prod.types.all()]),
            ', '.join([platform.name for platform in pouet_prod.platforms.all()]),
        ])


def candidates(request, year):
    exe_graphics = ProductionType.objects.get(internal_name='exe-graphics')

    prods = Production.objects.filter(
        Q(release_date_date__year=year)
        & (Q(supertype='production') | Q(types__path__startswith=exe_graphics.path))
    ).prefetch_related(
        'types', 'platforms', 'links', 'author_nicks', 'author_affiliation_nicks',
        'competition_placings__competition__party',
    ).order_by('sortable_title').distinct()

    pouet_prods = PouetProduction.objects.filter(
        Q(release_date_date__year=year)
    ).prefetch_related(
        'groups', 'platforms', 'types', 'competition_placings__party',
        'competition_placings__competition_type',
    )
    pouet_prods_by_id = {
        prod.pouet_id: prod
        for prod in pouet_prods
    }

    response = HttpResponse(content_type='text/plain;charset=utf-8')
    csvfile = csv.writer(response)
    csvfile.writerow([
        'pouet_url', 'demozoo_url', 'title', 'groups', 'thumbup', 'piggy', 'thumbdown', 'up-down',
        'avg', 'cdcs', 'popularity', 'party', 'type', 'platform',
    ])

    for prod in prods:
        pouet_ids = [link.parameter for link in prod.links.all() if link.link_class == 'PouetProduction']
        if len(pouet_ids) > 1:
            raise Exception("Multiple Pouet IDs for prod %d" % prod.id)
        elif pouet_ids:
            pouet_prod = pouet_prods_by_id.pop(int(pouet_ids[0]), None)
        else:
            pouet_prod = None

        write_row(csvfile, prod, pouet_prod)

    for pouet_prod in pouet_prods_by_id.values():
        write_row(csvfile, None, pouet_prod)

    return response
