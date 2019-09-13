from collections import defaultdict

from django.db.models import Q

from pouet.models import GroupMatchInfo, Production as PouetProduction
from productions.models import Production, ProductionLink, ProductionType


def get_match_data(releaser):
    music_prod_type = ProductionType.objects.get(internal_name='music')
    gfx_prod_type = ProductionType.objects.get(internal_name='graphics')
    exe_gfx_prod_type = ProductionType.objects.get(internal_name='exe-graphics')

    pouetable_prod_types = ProductionType.objects.exclude(
        Q(path__startswith=music_prod_type.path) |
        (Q(path__startswith=gfx_prod_type.path) & ~Q(path__startswith=exe_gfx_prod_type.path))
    )

    releaser_pouet_ids = [
        int(param)
        for param in releaser.external_links.filter(link_class='PouetGroup').values_list('parameter', flat=True)
    ]

    dz_prod_candidates = list(Production.objects.filter(
        (Q(author_nicks__releaser=releaser) | Q(author_affiliation_nicks__releaser=releaser)) &
        Q(types__in=pouetable_prod_types)
    ).distinct().only('id', 'title', 'supertype'))

    pouet_prod_candidates = list(
        PouetProduction.objects.filter(groups__pouet_id__in=releaser_pouet_ids).order_by('name')
    )

    matched_links = list(ProductionLink.objects.filter(
        Q(link_class='PouetProduction') &
        (
            Q(production__id__in=[prod.id for prod in dz_prod_candidates]) |
            Q(parameter__in=[prod.pouet_id for prod in pouet_prod_candidates])
        )
    ).select_related('production').order_by('production__title'))
    matched_pouet_ids = {int(link.parameter) for link in matched_links}
    matched_dz_ids = {link.production_id for link in matched_links}

    matched_pouet_prod_names_by_id = {
        prod.pouet_id: prod.name
        for prod in PouetProduction.objects.filter(pouet_id__in=matched_pouet_ids)
    }

    matched_prods = [
        (
            link.production_id,  # demozoo ID
            link.production.title,  # demozoo title
            link.production.get_absolute_url(),  # demozoo URL
            link.parameter,  # pouet ID
            matched_pouet_prod_names_by_id.get(int(link.parameter), "(Pouet prod #%s)" % link.parameter),  # pouet title with fallback
            "https://www.pouet.net/prod.php?which=%s" % link.parameter,
        )
        for link in matched_links
    ]

    unmatched_demozoo_prods = [
        (prod.id, prod.title, prod.get_absolute_url()) for prod in dz_prod_candidates
        if prod.id not in matched_dz_ids
    ]

    unmatched_pouet_prods = [
        (prod.pouet_id, prod.name, "https://www.pouet.net/prod.php?which=%d" % prod.pouet_id) for prod in pouet_prod_candidates
        if prod.pouet_id not in matched_pouet_ids
    ]

    return unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods


def automatch_productions(releaser):
    unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods = get_match_data(releaser)

    matched_production_count = len(matched_prods)
    unmatched_demozoo_production_count = len(unmatched_demozoo_prods)
    unmatched_pouet_production_count = len(unmatched_pouet_prods)

    # mapping of lowercased prod title to a pair of lists of demozoo IDs and pouet IDs of
    # prods with that name
    prods_by_name = defaultdict(lambda: ([], []))

    for id, title, url in unmatched_demozoo_prods:
        prods_by_name[title.lower()][0].append(id)

    for id, title, url in unmatched_pouet_prods:
        prods_by_name[title.lower()][1].append(id)

    for title, (demozoo_ids, pouet_ids) in prods_by_name.items():
        if len(demozoo_ids) == 1 and len(pouet_ids) == 1:
            ProductionLink.objects.create(
                production_id=demozoo_ids[0],
                link_class='PouetProduction',
                parameter=pouet_ids[0],
                is_download_link=False,
                source='auto',
            )
            matched_production_count += 1
            unmatched_demozoo_production_count -= 1
            unmatched_pouet_production_count -= 1

    GroupMatchInfo.objects.update_or_create(
        releaser_id=releaser.id, defaults={
            'matched_production_count': matched_production_count,
            'unmatched_demozoo_production_count': unmatched_demozoo_production_count,
            'unmatched_pouet_production_count': unmatched_pouet_production_count,
        }
    )
