from django.core.management.base import BaseCommand

from janeway.importing import import_author
from janeway.models import Author


class Command(BaseCommand):
    """Import authors from Janeway that don't correspond to any known Demozoo entries"""
    def handle(self, *args, **kwargs):
        creation_count = 0

        authors = Author.objects.raw("""
            SELECT janeway_author.*
            FROM
            (SELECT janeway_name.author_id, count(demoscene_nickvariant.name)
            FROM janeway_name
            LEFT JOIN demoscene_nickvariant on (lower(janeway_name.name) = lower(demoscene_nickvariant.name))
            GROUP BY janeway_name.author_id
            HAVING count(demoscene_nickvariant.name) = 0
            ) AS unseen_names
            INNER JOIN janeway_author ON (unseen_names.author_id = janeway_author.id)
            WHERE is_company = 'f'
            AND janeway_author.janeway_id NOT IN (
                select cast(parameter as int)
                from demoscene_releaserexternallink
                where link_class='KestraBitworldAuthor'
            )
        """)

        for (index, author) in enumerate(authors):
            if (index % 100 == 0):
                print("processed %d authors" % index)

            import_author(author)

            creation_count += 1

        print("%d authors created" % creation_count)
