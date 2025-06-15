from collections import defaultdict

from django.db.models import Q
from django.db.models.functions import Lower

from pouet.models import GroupMatchInfo
from pouet.models import Production as PouetProduction
from productions.models import Production, ProductionLink, ProductionType


def get_pouetable_prod_types():
    music_prod_type = ProductionType.objects.get(internal_name="music")
    gfx_prod_type = ProductionType.objects.get(internal_name="graphics")
    exe_gfx_prod_type = ProductionType.objects.get(internal_name="exe-graphics")

    return list(
        ProductionType.objects.exclude(
            Q(path__startswith=music_prod_type.path)
            | (Q(path__startswith=gfx_prod_type.path) & ~Q(path__startswith=exe_gfx_prod_type.path))
        ).values_list("id", flat=True)
    )


def get_nogroup_prods():
    pouet_prod_candidates_nogroups = list(
        PouetProduction.objects.filter(groups__isnull=True).order_by(Lower("name"))
    )

    matched_pouet_ids = list(
        ProductionLink.objects.filter(
            Q(link_class="PouetProduction")
            & Q(parameter__in=[prod.pouet_id for prod in pouet_prod_candidates_nogroups])
        ).values_list('parameter', flat=True)  # Get only the 'parameter' field
    )

    matched_pouet_ids_set = set(matched_pouet_ids)

    pouet_prod_candidates = [
        item for item in pouet_prod_candidates_nogroups if str(item.pouet_id) not in matched_pouet_ids_set
    ]

    nogroup_pouet_prods = [
        (prod.name, "https://www.pouet.net/prod.php?which=%d" % prod.pouet_id)
        for prod in pouet_prod_candidates
    ]

    return nogroup_pouet_prods


def get_match_data(releaser, pouetable_prod_types=None):
    if pouetable_prod_types is None:
        pouetable_prod_types = get_pouetable_prod_types()

    releaser_pouet_ids = [
        int(param)
        for param in releaser.external_links.filter(link_class="PouetGroup").values_list("parameter", flat=True)
    ]

    nick_ids = list(releaser.nicks.values_list("id", flat=True))
    dz_prod_candidates_query = Production.objects.raw(
        """
        SELECT DISTINCT
            "productions_production"."id", "productions_production"."title",
            "productions_production"."supertype", "productions_production"."sortable_title"
        FROM
            "productions_production"
            INNER JOIN "productions_production_types" ON (
                "productions_production"."id" = "productions_production_types"."production_id"
            )
        WHERE
            (
                productions_production.id in (
                    select production_id from productions_production_author_nicks where nick_id = ANY(%s)
                )
                OR productions_production.id in (
                    select production_id from productions_production_author_affiliation_nicks where nick_id = ANY(%s)
                )
            )
            AND "productions_production_types"."productiontype_id" = ANY(%s)
        ORDER BY
            productions_production.sortable_title
    """,
        [nick_ids, nick_ids, pouetable_prod_types],
    )
    dz_prod_candidates = list(dz_prod_candidates_query)

    pouet_prod_candidates = list(
        PouetProduction.objects.filter(groups__pouet_id__in=releaser_pouet_ids).order_by(Lower("name"))
    )

    matched_links = list(
        ProductionLink.objects.filter(
            Q(link_class="PouetProduction")
            & (
                Q(production__id__in=[prod.id for prod in dz_prod_candidates])
                | Q(parameter__in=[prod.pouet_id for prod in pouet_prod_candidates])
            )
        )
        .select_related("production")
        .order_by("production__title")
    )
    matched_pouet_ids = {int(link.parameter) for link in matched_links}
    matched_dz_ids = {link.production_id for link in matched_links}

    matched_pouet_prod_names_by_id = {
        prod.pouet_id: prod.name for prod in PouetProduction.objects.filter(pouet_id__in=matched_pouet_ids)
    }

    matched_prods = [
        (
            link.production_id,  # demozoo ID
            link.production.title,  # demozoo title
            link.production.get_absolute_url(),  # demozoo URL
            link.parameter,  # pouet ID
            matched_pouet_prod_names_by_id.get(
                int(link.parameter), "(Pouet prod #%s)" % link.parameter
            ),  # pouet title with fallback
            "https://www.pouet.net/prod.php?which=%s" % link.parameter,
        )
        for link in matched_links
    ]

    unmatched_demozoo_prods = [
        (prod.id, prod.title, prod.get_absolute_url()) for prod in dz_prod_candidates if prod.id not in matched_dz_ids
    ]

    unmatched_pouet_prods = [
        (prod.pouet_id, prod.name, "https://www.pouet.net/prod.php?which=%d" % prod.pouet_id)
        for prod in pouet_prod_candidates
        if prod.pouet_id not in matched_pouet_ids
    ]

    return unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods


def automatch_productions(releaser, pouetable_prod_types=None):
    unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods = get_match_data(
        releaser, pouetable_prod_types=pouetable_prod_types
    )

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
                link_class="PouetProduction",
                parameter=pouet_ids[0],
                is_download_link=False,
                source="auto",
            )
            matched_production_count += 1
            unmatched_demozoo_production_count -= 1
            unmatched_pouet_production_count -= 1

    GroupMatchInfo.objects.update_or_create(
        releaser_id=releaser.id,
        defaults={
            "matched_production_count": matched_production_count,
            "unmatched_demozoo_production_count": unmatched_demozoo_production_count,
            "unmatched_pouet_production_count": unmatched_pouet_production_count,
        },
    )
