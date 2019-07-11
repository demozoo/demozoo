from django.core.management.base import BaseCommand

from demoscene.models import Releaser, ReleaserExternalLink, Membership as DZMembership
from demoscene.utils.text import generate_search_title
from janeway.models import Author, Name


class Command(BaseCommand):
	"""Find group cross-links between Janeway and Demozoo data"""
	def handle(self, *args, **kwargs):
		creation_count = 0

		for (index, author) in enumerate(Author.objects.filter(is_group=True)):
			if (index % 100 == 0):
				print("processed %d groups" % index)

			# find releasers in the Demozoo data that match any of this author's names (excluding abbreviations)
			# and are groups
			candidate_releaser_ids = list(Releaser.objects.filter(
				is_group=True,
				nicks__variants__search_title__in=[generate_search_title(name.name) for name in author.names.all()]
			).distinct().values_list('id', flat=True))
			# print("-> %d name matches found: %r" % (len(candidate_releaser_ids), candidate_releaser_ids))

			if not candidate_releaser_ids:
				continue

			# get this group's member memberships
			member_ids = Author.objects.filter(group_memberships__group=author).values_list('janeway_id', flat=True)
			member_names = [
				generate_search_title(name.name)
				for name in Name.objects.filter(author__group_memberships__group=author)
			]

			member_demozoo_ids = list(ReleaserExternalLink.objects.filter(
				link_class='KestraBitworldAuthor', parameter__in=[str(id) for id in member_ids]
			).values_list('releaser_id', flat=True))
			# see if any candidate releasers have one or more matching members by ID
			matching_releaser_ids = set(DZMembership.objects.filter(
				group_id__in=candidate_releaser_ids,
				member_id__in=member_demozoo_ids
			).distinct().values_list('group_id', flat=True))

			# see if any candidate releasers have TWO or more matching members by name
			# (>=2 avoids false positives such as JP/Mayhem:
			#   http://janeway.exotica.org.uk/author.php?id=29340
			#   https://demozoo.org/sceners/40395/ )
			for candidate_releaser_id in candidate_releaser_ids:
				if candidate_releaser_id in matching_releaser_ids:
					# ignore ones which are already matched by member ID
					continue

				name_match_count = DZMembership.objects.filter(
					group_id=candidate_releaser_id,
					member__nicks__variants__search_title__in=member_names
				).distinct().values_list('member_id', flat=True).count()
				if name_match_count >= 2:
					print("group match: %s (%d) matches %d on %d member names" % (author.name, author.janeway_id, candidate_releaser_id, name_match_count))
					matching_releaser_ids.add(candidate_releaser_id)

			already_linked_releasers = list(ReleaserExternalLink.objects.filter(
				link_class='KestraBitworldAuthor', parameter=author.janeway_id
			).values_list('releaser_id', flat=True))

			for releaser_id in matching_releaser_ids:
				if releaser_id not in already_linked_releasers:
					ReleaserExternalLink.objects.create(
						releaser_id=releaser_id,
						link_class='KestraBitworldAuthor',
						parameter=author.janeway_id,
						source='janeway-automatch',
					)
					creation_count += 1

		print("%d cross-links created" % creation_count)
