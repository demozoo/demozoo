from demoscene.models import Releaser, ReleaserExternalLink
from demoscene.utils.text import generate_search_title


def get_dz_releaser_ids_matching_by_name_and_type(janeway_author):
	"""
	Return a list of Demozoo releaser IDs which match this Janeway author by at least one name,
	and are the same type (scener or group)
	"""
	names = [generate_search_title(name.name) for name in janeway_author.names.all()]
	return list(Releaser.objects.filter(
		is_group=janeway_author.is_group,
		nicks__variants__search_title__in=names,
	).distinct().values_list('id', flat=True))


def exclude_dz_releasers_with_crosslink(releaser_ids, janeway_author):
	"""
	Given a list of Demozoo releaser IDs, filter out the ones that have an existing
	cross-link to the given Janeway author
	"""
	already_linked_releasers = list(ReleaserExternalLink.objects.filter(
		link_class='KestraBitworldAuthor', parameter=janeway_author.janeway_id,
		releaser_id__in=releaser_ids
	).values_list('releaser_id', flat=True))

	return [i for i in releaser_ids if i not in already_linked_releasers]
