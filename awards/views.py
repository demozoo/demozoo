# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from awards.models import Event, Recommendation
from productions.models import Production
from read_only_mode import writeable_site_required


@require_POST
@login_required
@writeable_site_required
def recommend(request, event_id, production_id):
    production = get_object_or_404(Production, id=production_id)
    event = get_object_or_404(
        Event.accepting_recommendations_for(production), id=event_id
    )

    available_category_ids = event.categories.values_list('id', flat=True)
    selected_category_ids = [
        id for id in request.POST.getlist('category_id', [])
        if int(id) in available_category_ids
    ]
    unselected_category_ids = [
        id for id in available_category_ids
        if id not in selected_category_ids
    ]

    # delete recommendations for unchecked categories
    Recommendation.objects.filter(
        user=request.user, production=production, category_id__in=unselected_category_ids
    ).delete()

    # get-or-create recommendations for checked categories
    for category_id in selected_category_ids:
        Recommendation.objects.get_or_create(
            user=request.user, production=production, category_id=category_id
        )

    messages.success(request, "Thank you for your recommendation!")
    return HttpResponseRedirect(production.get_absolute_url())
