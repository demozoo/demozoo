# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render

from demoscene.models import Releaser
from pouet.matching import get_match_data
from productions.models import Production, ProductionLink, ProductionType


def groups(request):
	# get list of releasers who have PouetGroup cross-links
	releasers = Releaser.objects.filter(external_links__link_class='PouetGroup').order_by('name').distinct().only('name')
	return render(request, 'pouet/groups.html', {
		'releasers': releasers,
	})


def match_group(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)

	unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods = get_match_data(releaser)

	return render(request, 'pouet/match_group.html', {
		'releaser': releaser,
		'unmatched_demozoo_prods': unmatched_demozoo_prods,
		'unmatched_pouet_prods': unmatched_pouet_prods,
		'matched_prods': matched_prods,
	})
