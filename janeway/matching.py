from collections import defaultdict

from django.db.models import Q

from demoscene.models import Releaser, ReleaserExternalLink
from demoscene.utils.text import generate_search_title
from janeway.models import AuthorMatchInfo, Release as JanewayRelease
from platforms.models import Platform
from productions.models import Production, ProductionLink


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


def get_production_match_data(releaser):
	amiga_platform_ids = list(Platform.objects.filter(name__startswith='Amiga').values_list('id', flat=True))

	releaser_janeway_ids = [
		int(param)
		for param in releaser.external_links.filter(link_class='KestraBitworldAuthor').values_list('parameter', flat=True)
	]

	dz_prod_candidates = list(Production.objects.filter(
		(Q(author_nicks__releaser=releaser) | Q(author_affiliation_nicks__releaser=releaser)) &
		Q(platforms__in=amiga_platform_ids)
	).distinct().only('id', 'title', 'supertype'))

	janeway_release_candidates = list(
		JanewayRelease.objects.filter(author_names__author__janeway_id__in=releaser_janeway_ids).order_by('title')
	)

	matched_links = list(ProductionLink.objects.filter(
		Q(link_class='KestraBitworldRelease') &
		(
			Q(production__id__in=[prod.id for prod in dz_prod_candidates]) |
			Q(parameter__in=[prod.janeway_id for prod in janeway_release_candidates])
		)
	).select_related('production').order_by('production__title'))
	matched_janeway_ids = {int(link.parameter) for link in matched_links}
	matched_dz_ids = {link.production_id for link in matched_links}

	matched_janeway_release_names_by_id = {
		prod.janeway_id: prod.title
		for prod in JanewayRelease.objects.filter(janeway_id__in=matched_janeway_ids)
	}

	matched_prods = [
		(
			link.production_id,  # demozoo ID
			link.production.title,  # demozoo title
			link.production.get_absolute_url(),  # demozoo URL
			link.parameter,  # janeway ID
			matched_janeway_release_names_by_id.get(int(link.parameter), "(Janeway release #%s)" % link.parameter),  # Janeway title with fallback
			"http://janeway.exotica.org.uk/release.php?id=%s" % link.parameter,
			link.production.supertype,
		)
		for link in matched_links
	]

	unmatched_demozoo_prods = [
		(prod.id, prod.title, prod.get_absolute_url(), prod.supertype) for prod in dz_prod_candidates
		if prod.id not in matched_dz_ids
	]

	unmatched_janeway_releases = [
		(prod.janeway_id, prod.title, "http://janeway.exotica.org.uk/release.php?id=%d" % prod.janeway_id, prod.supertype) for prod in janeway_release_candidates
		if prod.janeway_id not in matched_janeway_ids
	]

	return unmatched_demozoo_prods, unmatched_janeway_releases, matched_prods


def automatch_productions(releaser):
	unmatched_demozoo_prods, unmatched_janeway_prods, matched_prods = get_production_match_data(releaser)

	matched_production_count = len(matched_prods)
	unmatched_demozoo_production_count = len(unmatched_demozoo_prods)
	unmatched_janeway_production_count = len(unmatched_janeway_prods)

	# mapping of lowercased prod title to a pair of lists of demozoo IDs and pouet IDs of
	# prods with that name
	prods_by_name_and_supertype = defaultdict(lambda: ([], []))

	for id, title, url, supertype in unmatched_demozoo_prods:
		prods_by_name_and_supertype[(title.lower(), supertype)][0].append(id)

	for id, title, url, supertype in unmatched_janeway_prods:
		prods_by_name_and_supertype[(title.lower(), supertype)][1].append(id)

	for (title, supertype), (demozoo_ids, janeway_ids) in prods_by_name_and_supertype.items():
		if len(demozoo_ids) == 1 and len(janeway_ids) == 1:
			ProductionLink.objects.create(
				production_id=demozoo_ids[0],
				link_class='KestraBitworldRelease',
				parameter=janeway_ids[0],
				is_download_link=False,
				source='janeway-automatch',
			)
			matched_production_count += 1
			unmatched_demozoo_production_count -= 1
			unmatched_janeway_production_count -= 1

	AuthorMatchInfo.objects.update_or_create(
		releaser_id=releaser.id, defaults={
			'matched_production_count': matched_production_count,
			'unmatched_demozoo_production_count': unmatched_demozoo_production_count,
			'unmatched_janeway_production_count': unmatched_janeway_production_count,
		}
	)
