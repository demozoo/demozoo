from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from demoscene.models import ReleaserExternalLink, Membership as DZMembership
from janeway import matching
from janeway.models import Author


class Command(BaseCommand):
    """Find scener cross-links between Janeway and Demozoo data"""
    def handle(self, *args, **kwargs):
        creation_count = 0

        for (index, author) in enumerate(Author.objects.filter(is_group=False)):
            if (index % 100 == 0):
                print("processed %d sceners" % index)

            # find sceners in the Demozoo data that match any of this author's names
            candidate_releaser_ids = matching.get_dz_releaser_ids_matching_by_name_and_type(author)
            # skip ones that already have a cross-link to this scener
            candidate_releaser_ids = matching.exclude_dz_releasers_with_crosslink(candidate_releaser_ids, author)

            if not candidate_releaser_ids:
                continue

            # get this scener's group memberships
            group_ids = author.get_group_ids()

            group_demozoo_ids = list(ReleaserExternalLink.objects.filter(
                link_class='KestraBitworldAuthor', parameter__in=[str(id) for id in group_ids]
            ).values_list('releaser_id', flat=True))
            # see if any candidate releasers have one or more matching groups by ID
            matching_releaser_ids = set(DZMembership.objects.filter(
                member_id__in=candidate_releaser_ids,
                group_id__in=group_demozoo_ids
            ).distinct().values_list('member_id', flat=True))

            group_names = author.get_group_clean_names()

            # see if any candidate releasers have TWO or more matching groups by name
            # (>=2 avoids false positives such as JP/Mayhem:
            #   http://janeway.exotica.org.uk/author.php?id=29340
            #   https://demozoo.org/sceners/40395/ )
            for candidate_releaser_id in candidate_releaser_ids:
                if candidate_releaser_id in matching_releaser_ids:
                    # ignore ones which are already matched by member ID
                    continue

                name_match_count = DZMembership.objects.filter(
                    member_id=candidate_releaser_id,
                    group__nicks__variants__search_title__in=group_names
                ).distinct().values_list('group_id', flat=True).count()
                if name_match_count >= 2:
                    print("scener match: %s (%d) matches %d on %d group names" % (author.name, author.janeway_id, candidate_releaser_id, name_match_count))
                    matching_releaser_ids.add(candidate_releaser_id)

            for releaser_id in matching_releaser_ids:
                ReleaserExternalLink.objects.create(
                    releaser_id=releaser_id,
                    link_class='KestraBitworldAuthor',
                    parameter=author.janeway_id,
                    source='janeway-automatch',
                )
                creation_count += 1

        print("%d cross-links created" % creation_count)
