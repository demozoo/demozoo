# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect

from demoscene.models import Edit, Releaser
from janeway.importing import import_release
from janeway.matching import get_production_match_data
from janeway.models import AuthorMatchInfo, Release as JanewayRelease
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


@writeable_site_required
@login_required
def production_import(request):
	if not request.user.is_staff:
		return redirect('home')
	release = get_object_or_404(JanewayRelease, janeway_id=request.POST['janeway_id'])

	production = import_release(release)

	Edit.objects.create(action_type='create_production', focus=production,
		description=(u"Added production '%s' from Janeway import" % production.title), user=request.user)

	return render(request, 'janeway/_matched_production.html', {
		'dz_id': production.id,
		'dz_title': production.title,
		'dz_url': production.get_absolute_url(),
		'janeway_id': release.janeway_id,
		'janeway_title': release.title,
		'janeway_url': "http://janeway.exotica.org.uk/release.php?id=%s" % release.janeway_id,
		'supertype': production.supertype,
	})


@writeable_site_required
@login_required
def import_all_author_productions(request):
	if not request.user.is_staff:
		return redirect('home')
	releaser = get_object_or_404(Releaser, id=request.POST['releaser_id'])
	unmatched_demozoo_prods, unmatched_janeway_prods, matched_prods = get_production_match_data(releaser)

	for janeway_id, title, url, supertype in unmatched_janeway_prods:
		import_release(JanewayRelease.objects.get(janeway_id=janeway_id))

	return redirect('janeway_match_author', releaser.id)
