import itertools

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from read_only_mode import writeable_site_required

from awards.models import Event, Recommendation
from demoscene.shortcuts import get_page
from productions.models import Production


@require_POST
@login_required
@writeable_site_required
def recommend(request, event_slug, production_id):
    production = get_object_or_404(Production, id=production_id)
    event = get_object_or_404(
        Event.accepting_recommendations_for(production), slug=event_slug
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


def user_recommendations(request, event_slug):
    event = get_object_or_404(
        Event.active_for_user(request.user), slug=event_slug
    )

    if request.user.is_authenticated:
        recommendations = Recommendation.objects.filter(
            user=request.user, category__event=event
        ).select_related('category', 'production').prefetch_related(
            'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser'
        ).order_by('category', 'production__sortable_title')

        recommendations_by_category = [
            (category, list(recs))
            for category, recs in itertools.groupby(recommendations, lambda r: r.category)
        ]
    else:
        recommendations_by_category = []

    return render(request, 'awards/user_recommendations.html', {
        'event': event,
        'recommendations_by_category': recommendations_by_category,
        'can_view_reports': event.user_can_view_reports(request.user),
        'can_remove_recommendations': event.recommendations_enabled,
    })


@require_POST
@login_required
@writeable_site_required
def remove_recommendation(request, recommendation_id):
    recommendation = get_object_or_404(
        Recommendation.objects.filter(user=request.user, category__event__recommendations_enabled=True),
        id=recommendation_id
    )

    recommendation.delete()
    return HttpResponseRedirect(reverse('awards_user_recommendations', args=(recommendation.category.event.slug, )))


@login_required
def report(request, event_slug, category_id):
    event = get_object_or_404(
        Event.objects.filter(reporting_enabled=True), slug=event_slug
    )
    category = get_object_or_404(
        event.categories.all(), id=category_id
    )
    if not event.user_can_view_reports(request.user):
        raise PermissionDenied

    productions = category.get_recommendation_report().prefetch_related(
        'author_nicks__releaser', 'author_affiliation_nicks__releaser'
    )

    return render(request, 'awards/report.html', {
        'event': event,
        'category': category,
        'productions': productions,
    })


def candidates(request, event_slug, category_slug):
    event = get_object_or_404(
        Event.objects.filter(recommendations_enabled=True), slug=event_slug
    )
    category = get_object_or_404(
        event.categories.all(), slug=category_slug
    )

    productions = category.eligible_productions().prefetch_related(
        'author_nicks__releaser', 'author_affiliation_nicks__releaser',
        'types', 'platforms',
    ).order_by('sortable_title')

    production_page = get_page(
        productions,
        request.GET.get('page', '1'))

    return render(request, 'awards/candidates.html', {
        'event': event,
        'category': category,
        'production_page': production_page,
    })
