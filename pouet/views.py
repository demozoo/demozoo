# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, render

from demoscene.models import Releaser
from pouet.matching import get_match_data
from pouet.models import GroupMatchInfo


def groups(request):
	# get list of releasers who have Pouet.GroupMatchInfo data
	groups = GroupMatchInfo.objects.select_related('releaser').order_by('releaser__name').prefetch_related('releaser__nicks')
	show_full = request.GET.get('full')

	if not show_full:
		# filter to just the ones which have unmatched entries on both sides
		groups = groups.filter(unmatched_demozoo_production_count__gt=0, unmatched_pouet_production_count__gt=0)

	return render(request, 'pouet/groups.html', {
		'groups': groups,
		'showing_full': show_full,
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
