import itertools

from django.db import transaction
from django.db.models import Max

from demoscene.models import Releaser, ReleaserExternalLink
from platforms.models import Platform
from productions.models import Production, ProductionLink, ProductionType


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


def get_best_nick(releaser, name):
	"""
	Return the Nick object from this releaser's nicks which best matches the given name;
	look for exact matches first, then case-insensitive matches, then fall back on
	primary nick
	"""
	# look for an exact nick match
	nick = releaser.nicks.filter(variants__name=name).first()

	# failing that, look for a case-insensitive nick match
	if nick is None:
		nick = releaser.nicks.filter(variants__name__iexact=name).first()

	# failing that, just use the primary nick
	if nick is None:
		nick = releaser.primary_nick

	return nick


def get_nick_for_name(name):
	"""
	Given a Janeway name object, find the corresponding Demozoo releaser and return its best
	corresponding nick object, or None if no such releaser (or multiple releasers) exists
	"""
	try:
		releaser_link = ReleaserExternalLink.objects.get(
			link_class='KestraBitworldAuthor', parameter=name.author.janeway_id
		)
	except (ReleaserExternalLink.DoesNotExist, ReleaserExternalLink.MultipleObjectsReturned):
		return None

	return get_best_nick(releaser_link.releaser, name.name)


def import_release(release):
	with transaction.atomic():
		prod = Production.objects.create(
			title=release.title,
			supertype=release.supertype,
			data_source='janeway'
		)
		prod.links.create(
			link_class='KestraBitworldRelease', parameter=release.janeway_id, is_download_link=False
		)

		for author_name in release.author_names.all():
			nick = get_nick_for_name(author_name)
			if nick:
				prod.author_nicks.add(nick)

		if release.platform == 'ocs':
			prod.platforms.add(Platform.objects.get(name='Amiga OCS/ECS'))
		elif release.platform == 'aga':
			prod.platforms.add(Platform.objects.get(name='Amiga AGA'))
		elif release.platform == 'ppc':
			prod.platforms.add(Platform.objects.get(name='Amiga PPC/RTG'))

		for prod_type in release.types.all():
			prod.types.add(ProductionType.objects.get(name=prod_type.type_name))

		credits = release.credits.order_by('name_id', 'category')
		# merge credits with the same nick and category into one entry;
		# do this by forming a tuple of (resolved nick, category) for each credit and grouping on that
		for (nick, category), credits_for_nick in itertools.groupby(
			credits, lambda credit: (get_nick_for_name(credit.name), credit.category)
		):
			if not nick:
				continue

			# merge all non-empty descriptions into one string
			descriptions = filter(bool, [credit.description for credit in credits_for_nick])
			description = ', '.join(descriptions)
			prod.credits.create(
				data_source='janeway',
				nick=nick,
				category=category,
				role=description
			)

		for download_link in release.download_links.all():
			link = ProductionLink(
				production=prod,
				is_download_link=True,
				source='janeway',
				description=download_link.comment
			)
			link.url = download_link.url
			link.save()

		# import pack contents (when this release is a pack)
		pack_member_index = 1
		for pack_member in release.pack_contents.select_related('content').order_by('id'):

			# look for a Demozoo record for a prod with this Janeway reference
			try:
				pack_member_link = ProductionLink.objects.get(
					link_class='KestraBitworldRelease', parameter=pack_member.content.janeway_id
				)
			except (ProductionLink.DoesNotExist, ProductionLink.MultipleObjectsReturned):
				continue

			prod.pack_members.create(
				data_source='janeway',
				member_id=pack_member_link.production_id,
				position=pack_member_index
			)
			pack_member_index += 1

		# import packs that this release is packed in
		for pack_rel in release.packed_in.select_related('pack').order_by('id'):

			# look for a Demozoo record for a prod with this Janeway reference
			try:
				pack_link = ProductionLink.objects.get(
					link_class='KestraBitworldRelease', parameter=pack_rel.pack.janeway_id
				)
			except (ProductionLink.DoesNotExist, ProductionLink.MultipleObjectsReturned):
				continue

			next_position = pack_link.production.pack_members.aggregate(pos=Max('position'))['pos'] + 1

			pack_link.production.pack_members.create(
				data_source='janeway',
				member=prod,
				position=next_position
			)

		# import soundtrack links (for soundtracks in this prod)
		soundtrack_index = 1
		for soundtrack_rel in release.soundtrack_links.select_related('soundtrack').order_by('id'):

			# look for a Demozoo record for a prod with this Janeway reference
			try:
				soundtrack_link = ProductionLink.objects.get(
					link_class='KestraBitworldRelease', parameter=soundtrack_rel.soundtrack.janeway_id
				)
			except (ProductionLink.DoesNotExist, ProductionLink.MultipleObjectsReturned):
				continue

			prod.soundtrack_links.create(
				data_source='janeway',
				soundtrack_id=soundtrack_link.production_id,
				position=soundtrack_index
			)
			soundtrack_index += 1

		# import soundtrack links (for prods that this is the soundtrack for)
		for soundtrack_rel in release.appearances_as_soundtrack.select_related('release').order_by('id'):

			# look for a Demozoo record for a prod with this Janeway reference
			try:
				prod_link = ProductionLink.objects.get(
					link_class='KestraBitworldRelease', parameter=soundtrack_rel.release.janeway_id
				)
			except (ProductionLink.DoesNotExist, ProductionLink.MultipleObjectsReturned):
				continue

			next_position = prod_link.production.soundtrack_links.aggregate(pos=Max('position'))['pos'] + 1

			prod_link.production.soundtrack_links.create(
				data_source='janeway',
				soundtrack=prod,
				position=next_position
			)

		return prod
