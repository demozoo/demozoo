from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from demoscene.models import Edit
from demoscene.models import Membership as DZMembership
from demoscene.models import ReleaserExternalLink
from janeway.models import Membership


class Command(BaseCommand):
    """Find and add memberships in Janeway data which are not present in Demozoo"""
    def handle(self, *args, **kwargs):
        creation_count = 0

        for membership in Membership.objects.all():
            # Look for a unique Demozoo entry for both the group and the member
            try:
                group_link = ReleaserExternalLink.objects.get(
                    link_class='KestraBitworldAuthor', parameter=membership.group.janeway_id
                )
            except (ReleaserExternalLink.DoesNotExist, ReleaserExternalLink.MultipleObjectsReturned):
                continue

            group = group_link.releaser

            try:
                member_link = ReleaserExternalLink.objects.get(
                    link_class='KestraBitworldAuthor', parameter=membership.member.janeway_id
                )
            except (ReleaserExternalLink.DoesNotExist, ReleaserExternalLink.MultipleObjectsReturned):
                continue

            member = member_link.releaser

            # skip if link already exists
            if DZMembership.objects.filter(member=member, group=group).exists():
                continue

            # skip if this membership was previously deleted
            if Edit.objects.filter(
                action_type='remove_membership', focus_object_id=member.id, focus2_object_id=group.id
            ).exists():
                print("Skipping membership %s of %s, as it was previously deleted" % (member.name, group.name))
                continue

            is_current = membership.until is not None
            print("Adding membership: %s of %s. Current: %r" % (member.name, group.name, is_current))
            DZMembership.objects.create(
                member=member, group=group, is_current=is_current, data_source='janeway'
            )
            creation_count += 1

        print("%d memberships added" % creation_count)
