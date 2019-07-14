# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from demoscene.models import Edit, Releaser
from janeway.matching import get_production_match_data
from janeway.models import AuthorMatchInfo
from productions.models import Production, ProductionLink
from read_only_mode import writeable_site_required


@login_required
def authors(request):
	# get list of releasers who have Pouet.GroupMatchInfo data
	authors = AuthorMatchInfo.objects.select_related('releaser').order_by('releaser__name').prefetch_related('releaser__nicks')
	show_full = request.GET.get('full')

	if not show_full:
		# filter to just the ones which have unmatched entries on both sides
		authors = authors.filter(unmatched_demozoo_production_count__gt=0, unmatched_janeway_production_count__gt=0)

	return render(request, 'janeway/authors.html', {
		'authors': authors,
		'showing_full': show_full,
	})


@login_required
def match_author(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)

	unmatched_demozoo_prods, unmatched_janeway_prods, matched_prods = get_production_match_data(releaser)

	return render(request, 'janeway/match_author.html', {
		'releaser': releaser,
		'unmatched_demozoo_prods': unmatched_demozoo_prods,
		'unmatched_janeway_prods': unmatched_janeway_prods,
		'matched_prods': matched_prods,
	})


@writeable_site_required
@login_required
def production_link(request):
	production = get_object_or_404(Production, id=request.POST['demozoo_id'])
	janeway_id = request.POST['janeway_id']

	(link, created) = ProductionLink.objects.get_or_create(
		link_class='KestraBitworldRelease',
		parameter=janeway_id,
		production=production,
		is_download_link=False,
		source='match',
	)
	if created:
		Edit.objects.create(action_type='production_add_external_link', focus=production,
			description=(u"Added Kestra Bitworld link to ID %s" % janeway_id), user=request.user)

	return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def production_unlink(request):
	production = get_object_or_404(Production, id=request.POST['demozoo_id'])
	janeway_id = request.POST['janeway_id']

	links = ProductionLink.objects.filter(
		link_class='KestraBitworldRelease',
		parameter=janeway_id,
		production=production)
	if links:
		Edit.objects.create(action_type='production_delete_external_link', focus=production,
			description=(u"Deleted Kestra Bitworld link to ID %s" % janeway_id), user=request.user)
		links.delete()

	return HttpResponse("OK", content_type="text/plain")
