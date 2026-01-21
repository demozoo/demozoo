from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

from awards.models import ScreeningDecision
from demoscene.models import Releaser
from productions.models import ProductionType


class Command(BaseCommand):
    help = "Generate a listing of candidates for the Meteoriks New Talent award"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Year to generate report for")
        parser.add_argument("--exclude-compo-id", type=int, action="append", help="ID of compo to exclude from report")

    def handle(self, *args, **options):
        year = options["year"]
        exclude_compo_ids = list(options["exclude_compo_id"] or (-999,))
        exe_gfx_ids = list(
            ProductionType.objects.filter(
                path__startswith=ProductionType.objects.get(internal_name="exe-graphics").path
            ).values_list("id", flat=True)
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
SELECT DISTINCT releaser_id FROM (
    SELECT demoscene_nick.releaser_id
    FROM productions_production
    INNER JOIN productions_production_author_nicks ON (
        productions_production.id = productions_production_author_nicks.production_id
    )
    INNER JOIN demoscene_nick ON (
        productions_production_author_nicks.nick_id = demoscene_nick.id
    )
    LEFT JOIN productions_production_types ON (
        productions_production.id = productions_production_types.production_id
    )
    WHERE
        EXTRACT(YEAR FROM release_date_date) = %(year)s
        AND (
            productions_production.supertype = 'production'
            OR productions_production_types.productiontype_id = ANY(%(exe_gfx_ids)s)
        )
        AND productions_production.id NOT IN (
            SELECT production_id FROM parties_competitionplacing WHERE competition_id = ANY(%(exclude_compo_ids)s)
        )
    GROUP BY demoscene_nick.releaser_id
    UNION
    SELECT demoscene_nick.releaser_id
    FROM productions_production
    INNER JOIN productions_credit ON (
        productions_production.id = productions_credit.production_id
    )
    INNER JOIN demoscene_nick ON (
        productions_credit.nick_id = demoscene_nick.id
    )
    LEFT JOIN productions_production_types ON (
        productions_production.id = productions_production_types.production_id
    )
    WHERE
        EXTRACT(YEAR FROM release_date_date) = %(year)s
        AND (
            productions_production.supertype = 'production'
            OR productions_production_types.productiontype_id = ANY(%(exe_gfx_ids)s)
        )
        AND productions_production.id NOT IN (
            SELECT production_id FROM parties_competitionplacing WHERE competition_id = ANY(%(exclude_compo_ids)s)
        )
    GROUP BY demoscene_nick.releaser_id
) AS releasers_this_year;
            """,
                {"year": year, "exe_gfx_ids": exe_gfx_ids, "exclude_compo_ids": exclude_compo_ids},
            )
            releasers_this_year = [releaser_id for (releaser_id,) in cursor.fetchall()]

        for releaser_id in releasers_this_year:
            releaser = Releaser.objects.get(id=releaser_id)
            prod_ids = set()
            is_eligible = True

            author_prods = (
                releaser.productions()
                .filter(Q(supertype="production") | Q(types__in=exe_gfx_ids))
                .values_list("id", "release_date_date")
            )
            for prod_id, rel_date in author_prods:
                if not rel_date or rel_date.year < year:
                    is_eligible = False
                    break
                prod_ids.add(prod_id)
            if not is_eligible:
                continue

            affil_prods = (
                releaser.member_productions()
                .filter(Q(supertype="production") | Q(types__in=exe_gfx_ids))
                .values_list("id", "release_date_date")
            )
            for prod_id, rel_date in affil_prods:
                if not rel_date or rel_date.year < year:
                    is_eligible = False
                    break
                prod_ids.add(prod_id)
            if not is_eligible:
                continue

            credit_prods = (
                releaser.credits()
                .filter(Q(production__supertype="production") | Q(production__types__in=exe_gfx_ids))
                .values_list("production_id", "production__release_date_date")
            )
            for prod_id, rel_date in credit_prods:
                if not rel_date or rel_date.year < year:
                    is_eligible = False
                    break
                prod_ids.add(prod_id)
            if not is_eligible:
                continue

            yay_count = ScreeningDecision.objects.filter(
                production_id__in=prod_ids,
                is_accepted=True,
            ).count()

            print("%s,https://demozoo.org%s,%d" % (releaser.name, releaser.get_absolute_url(), yay_count))
