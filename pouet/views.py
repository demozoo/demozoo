# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from demoscene.models import Edit, Releaser
from pouet.matching import get_match_data
from pouet.models import GroupMatchInfo
from productions.models import Production, ProductionLink
from read_only_mode import writeable_site_required


@login_required
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


@login_required
def match_group(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods = get_match_data(releaser)

    return render(request, 'pouet/match_group.html', {
        'releaser': releaser,
        'unmatched_demozoo_prods': unmatched_demozoo_prods,
        'unmatched_pouet_prods': unmatched_pouet_prods,
        'matched_prods': matched_prods,
    })


@writeable_site_required
@login_required
def production_link(request):
    production = get_object_or_404(Production, id=request.POST['demozoo_id'])
    pouet_id = request.POST['pouet_id']

    (link, created) = ProductionLink.objects.get_or_create(
        link_class='PouetProduction',
        parameter=pouet_id,
        production=production,
        is_download_link=False,
        source='match',
    )
    if created:
        Edit.objects.create(action_type='production_add_external_link', focus=production,
            description=(u"Added Pouet link to ID %s" % pouet_id), user=request.user)

    return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def production_unlink(request):
    production = get_object_or_404(Production, id=request.POST['demozoo_id'])
    pouet_id = request.POST['pouet_id']

    links = ProductionLink.objects.filter(
        link_class='PouetProduction',
        parameter=pouet_id,
        production=production)
    if links:
        Edit.objects.create(action_type='production_delete_external_link', focus=production,
            description=(u"Deleted Pouet link to ID %s" % pouet_id), user=request.user)
        links.delete()

    return HttpResponse("OK", content_type="text/plain")
