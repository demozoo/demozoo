import requests
from django.core.management.base import BaseCommand

from demoscene.models import Releaser, ReleaserExternalLink
from productions.models import Production, ProductionLink


# Add scene.graphics cross-links from https://scene.graphics/api/v1/demozoo/links
# where they do not already exist


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        verbose = kwargs["verbosity"] >= 1

        if verbose:
            print("Fetching scene.graphics links...")
        response = requests.get("https://scene.graphics/api/v1/demozoo/links").json()

        if verbose:
            print("Adding production links from scene.graphics...")
        links = [link for link in response.get("productions", []) if not link["url"].startswith("/windows/")]
        prods_with_existing_links = set(
            ProductionLink.objects.filter(link_class="ScenegraphicsProduction")
            .values_list("production_id", flat=True)
            .distinct()
        )
        ids_in_import = [link["demozoo_id"] for link in links]
        valid_ids = set(Production.objects.filter(id__in=ids_in_import).values_list("id", flat=True))

        added_count = 0
        for link in links:
            production_id = link["demozoo_id"]
            parameter = link["url"].lstrip("/")
            if production_id in prods_with_existing_links:
                continue
            if production_id not in valid_ids:
                if verbose:
                    print(f"Skipping invalid production ID {production_id}")
                continue
            ProductionLink.objects.create(
                production_id=production_id,
                link_class="ScenegraphicsProduction",
                parameter=parameter,
                is_download_link=False,
                source="import",
            )
            added_count += 1
            if added_count % 1000 == 0 and verbose:  # pragma: no cover
                print(f"Added {added_count} production links")

        if verbose:
            print("Adding group links from scene.graphics...")
        links = response.get("groups", [])
        groups_with_existing_links = set(
            ReleaserExternalLink.objects.filter(link_class="ScenegraphicsGroup")
            .values_list("releaser_id", flat=True)
            .distinct()
        )
        ids_in_import = [link["demozoo_id"] for link in links]
        valid_ids = set(Releaser.objects.filter(id__in=ids_in_import, is_group=True).values_list("id", flat=True))

        added_count = 0
        for link in links:
            group_id = link["demozoo_id"]
            parameter = link["url"].split("/")[-1]
            if group_id in groups_with_existing_links:
                continue
            if group_id not in valid_ids:
                if verbose:
                    print(f"Skipping invalid group ID {group_id}")
                continue
            ReleaserExternalLink.objects.create(
                releaser_id=group_id,
                link_class="ScenegraphicsGroup",
                parameter=parameter,
                source="import",
            )
            added_count += 1
            if added_count % 1000 == 0 and verbose:  # pragma: no cover
                print(f"Added {added_count} group links")

        if verbose:
            print("Adding scener links from scene.graphics...")
        links = response.get("sceners", [])
        sceners_with_existing_links = set(
            ReleaserExternalLink.objects.filter(link_class="ScenegraphicsScener")
            .values_list("releaser_id", flat=True)
            .distinct()
        )
        ids_in_import = [link["demozoo_id"] for link in links]
        valid_ids = set(Releaser.objects.filter(id__in=ids_in_import, is_group=False).values_list("id", flat=True))

        added_count = 0
        for link in response.get("sceners", []):
            scener_id = link["demozoo_id"]
            parameter = link["url"].split("/")[-1]
            if scener_id in sceners_with_existing_links:
                continue
            if scener_id not in valid_ids:
                if verbose:
                    print(f"Skipping invalid scener ID {scener_id}")
                continue
            ReleaserExternalLink.objects.create(
                releaser_id=scener_id,
                link_class="ScenegraphicsScener",
                parameter=parameter,
                source="import",
            )
            added_count += 1
            if added_count % 1000 == 0 and verbose:  # pragma: no cover
                print(f"Added {added_count} scener links")
