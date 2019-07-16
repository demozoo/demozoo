from django.db import transaction

from demoscene.models import Releaser, ReleaserExternalLink


def import_author(author):
	with transaction.atomic():
		releaser = Releaser.objects.create(
			name=author.name,
			is_group=author.is_group,
			data_source='janeway'
		)
		releaser.external_links.create(
			link_class='KestraBitworldAuthor', parameter=author.janeway_id
		)

		for name in author.names.all():
			if name.name.lower() != author.name.lower():
				releaser.nicks.create(
					name=name.name,
					abbreviation=name.abbreviation or ''
				)
			elif name.abbreviation:
				primary_nick = releaser.primary_nick
				primary_nick.abbreviation = name.abbreviation
				primary_nick.save()

		for membership in author.group_memberships.all():
			# look for a Demozoo record with this Janeway reference
			try:
				group_link = ReleaserExternalLink.objects.get(
					link_class='KestraBitworldAuthor', parameter=membership.group.janeway_id
				)
			except (ReleaserExternalLink.DoesNotExist, ReleaserExternalLink.MultipleObjectsReturned):
				continue

			releaser.group_memberships.create(
				group_id=group_link.releaser_id,
				is_current=(membership.until is None),
				data_source='janeway'
			)

		for membership in author.member_memberships.all():
			# look for a Demozoo record with this Janeway reference
			try:
				member_link = ReleaserExternalLink.objects.get(
					link_class='KestraBitworldAuthor', parameter=membership.member.janeway_id
				)
			except (ReleaserExternalLink.DoesNotExist, ReleaserExternalLink.MultipleObjectsReturned):
				continue

			releaser.member_memberships.create(
				member_id=member_link.releaser_id,
				is_current=(membership.until is None),
				data_source='janeway'
			)
