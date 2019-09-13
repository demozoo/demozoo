from django.core.management.base import BaseCommand

from productions.models import Production


class Command(BaseCommand):
    """Fill in release dates from Janeway on productions that don't have one listed"""
    def handle(self, *args, **kwargs):
        prods = Production.objects.raw("""
            SELECT productions_production.id, janeway_release.release_date_date, janeway_release.release_date_precision
            FROM productions_production
            INNER JOIN productions_productionlink ON (
                productions_production.id = productions_productionlink.production_id
                AND link_class = 'KestraBitworldRelease'
            )
            INNER JOIN janeway_release ON (
                CAST(productions_productionlink.parameter AS int) = janeway_release.janeway_id
                AND janeway_release.release_date_date IS NOT NULL
            )
            WHERE productions_production.release_date_date IS NULL
        """)

        for (index, prod) in enumerate(prods):
            if (index % 100 == 0):
                print("added %d release dates" % index)

            Production.objects.filter(id=prod.id).update(release_date_date=prod.release_date_date, release_date_precision=prod.release_date_precision)

        print("%d release dates added." % (index + 1))
