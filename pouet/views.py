from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render


from common.views import writeable_site_required
from demoscene.models import Edit, Releaser
from pouet.matching import get_match_data, get_nogroup_prods
from pouet.models import GroupMatchInfo
from productions.models import Production, ProductionLink


@login_required
def groups(request):
    # get list of releasers who have Pouet.GroupMatchInfo data
    groups = (
        GroupMatchInfo.objects.select_related("releaser").order_by("releaser__name").prefetch_related("releaser__nicks")
    )
    # mode = matchable, pouet_unmatched or all
    mode = request.GET.get("mode", "matchable")

    if mode == "matchable":
        # filter to just the ones which have unmatched entries on both sides
        groups = groups.filter(unmatched_demozoo_production_count__gt=0, unmatched_pouet_production_count__gt=0)
    elif mode == "pouet_unmatched":
        # filter to the ones which have unmatched entries on Pouet
        groups = groups.filter(unmatched_pouet_production_count__gt=0)

    return render(
        request,
        "pouet/groups.html",
        {
            "groups": groups,
            "mode": mode,
        },
    )


@login_required
def nogroup_prods(request):
    # get list of prods with no releasers
    nogroup_prods = get_nogroup_prods()
    nogroup_prods_amount = len(nogroup_prods)

    return render(
        request,
        "pouet/nogroup-prods.html",
        {
            'nogroup_prods_amount': nogroup_prods_amount,
            'nogroup_prods': nogroup_prods,
        }
    )


@login_required
def match_group(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    unmatched_demozoo_prods, unmatched_pouet_prods, matched_prods = get_match_data(releaser)

    return render(
        request,
        "pouet/match_group.html",
        {
            "releaser": releaser,
            "unmatched_demozoo_prods": unmatched_demozoo_prods,
            "unmatched_pouet_prods": unmatched_pouet_prods,
            "matched_prods": matched_prods,
        },
    )


@writeable_site_required
@login_required
def production_link(request):
    production = get_object_or_404(Production, id=request.POST["demozoo_id"])
    pouet_id = request.POST["pouet_id"]

    (link, created) = ProductionLink.objects.get_or_create(
        link_class="PouetProduction",
        parameter=pouet_id,
        production=production,
        is_download_link=False,
        source="match",
    )
    if created:
        Edit.objects.create(
            action_type="production_add_external_link",
            focus=production,
            description=("Added Pouet link to ID %s" % pouet_id),
            user=request.user,
        )

    return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def production_unlink(request):
    production = get_object_or_404(Production, id=request.POST["demozoo_id"])
    pouet_id = request.POST["pouet_id"]

    links = ProductionLink.objects.filter(link_class="PouetProduction", parameter=pouet_id, production=production)
    if links:
        Edit.objects.create(
            action_type="production_delete_external_link",
            focus=production,
            description=("Deleted Pouet link to ID %s" % pouet_id),
            user=request.user,
        )
        links.delete()

    return HttpResponse("OK", content_type="text/plain")
