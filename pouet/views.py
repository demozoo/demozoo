# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from demoscene.models import Releaser
from productions.models import Production, ProductionType


def groups(request):
	# get list of releasers who have PouetGroup cross-links
	releasers = Releaser.objects.filter(external_links__link_class='PouetGroup').order_by('name').distinct().only('name')
	return render(request, 'pouet/groups.html', {
		'releasers': releasers,
	})


def match_group(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)

	music_prod_type = ProductionType.objects.get(internal_name='music')
	gfx_prod_type = ProductionType.objects.get(internal_name='graphics')
	exe_gfx_prod_type = ProductionType.objects.get(internal_name='exe-graphics')

	pouetable_prod_types = ProductionType.objects.exclude(
		Q(path__startswith=music_prod_type.path) |
		(Q(path__startswith=gfx_prod_type.path) & ~Q(path__startswith=exe_gfx_prod_type.path))
	)

	releaser_prods = Production.objects.filter(
		(Q(author_nicks__releaser=releaser) | Q(author_affiliation_nicks__releaser=releaser)) &
		Q(types__in=pouetable_prod_types)
	).distinct()

	matched_prods = releaser_prods.filter(
		Q(links__link_class='PouetProduction')
	).order_by('title').only('title', 'supertype')

	matched_prod_ids = [prod.id for prod in matched_prods]
	unmatched_prods = releaser_prods.exclude(
		id__in=matched_prod_ids
	).order_by('title').only('title', 'supertype')

	return render(request, 'pouet/match_group.html', {
		'releaser': releaser,
		'matched_prods': matched_prods,
		'unmatched_prods': unmatched_prods,
	})
