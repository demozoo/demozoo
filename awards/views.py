import itertools

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from awards.forms import ScreeningCommentForm, ScreeningFilterForm
from awards.models import Event, Nomination, Recommendation, ScreeningComment
from common.utils.pagination import PaginationControls
from common.views import writeable_site_required
from demoscene.shortcuts import get_page
from productions.carousel import Carousel
from productions.models import Production, Screenshot
from productions.panels import DownloadsPanel


@require_POST
@login_required
@writeable_site_required
def recommend(request, event_slug, production_id):
    production = get_object_or_404(Production, id=production_id)
    event = get_object_or_404(Event.accepting_recommendations_for(production), slug=event_slug)

    available_category_ids = event.categories.values_list("id", flat=True)
    selected_category_ids = [id for id in request.POST.getlist("category_id", []) if int(id) in available_category_ids]
    unselected_category_ids = [id for id in available_category_ids if id not in selected_category_ids]

    # delete recommendations for unchecked categories
    Recommendation.objects.filter(
        user=request.user, production=production, category_id__in=unselected_category_ids
    ).delete()

    # get-or-create recommendations for checked categories
    for category_id in selected_category_ids:
        Recommendation.objects.get_or_create(user=request.user, production=production, category_id=category_id)

    messages.success(request, "Thank you for your recommendation!")
    return HttpResponseRedirect(production.get_absolute_url())


def show(request, event_slug):
    # The main award page at /awards/[event_slug]/ :
    # * If nominees exist, show the results
    # * If user is a juror:
    #   * if reports are enabled, show the links to the per-category recommendation reports
    #   * if screening is enabled, show the link to the screening interface
    # * If user is logged in and recommendations are enabled, show the user's recommendations

    event = get_object_or_404(Event, slug=event_slug)
    nominations = (
        Nomination.objects.filter(category__event=event)
        .select_related("category")
        .prefetch_related(
            "production__author_nicks__releaser",
            "production__author_affiliation_nicks__releaser",
            "production__platforms",
            "production__types",
        )
        .order_by("category__position", "category__name", "category__id", "-status", "production__title")
    )
    production_ids = {nom.production_id for nom in nominations}
    screenshots = Screenshot.select_for_production_ids(production_ids)

    nominations_by_category = []
    for category, category_nominations in itertools.groupby(nominations, lambda r: r.category):
        status_groups = [
            (status, [(nom.production, screenshots.get(nom.production.id)) for nom in noms])
            for status, noms in itertools.groupby(category_nominations, lambda r: r.status)
        ]
        nominations_by_category.append((category, status_groups))

    if nominations and event.series_id:
        # look for other events in the series that have nominations
        other_events = (
            Event.objects.filter(series_id=event.series_id)
            .annotate(num_nominations=models.Count("categories__nominations"))
            .filter(num_nominations__gt=0)
            .order_by("eligibility_start_date")
        )
    else:
        other_events = []

    if request.user.is_authenticated and event.recommendations_enabled:
        recommendations = (
            Recommendation.objects.filter(user=request.user, category__event=event)
            .select_related("category", "production")
            .prefetch_related("production__author_nicks__releaser", "production__author_affiliation_nicks__releaser")
            .order_by("category", "production__sortable_title")
        )

        recommendations_by_category = [
            (category, list(recs)) for category, recs in itertools.groupby(recommendations, lambda r: r.category)
        ]
    else:
        recommendations_by_category = []

    can_access_screening = event.user_can_access_screening(request.user)
    if can_access_screening:
        screened_by_me_count = event.screening_decisions.filter(user=request.user).count()
        screening_filter_form = ScreeningFilterForm(event, initial=request.GET)
    else:
        screened_by_me_count = None
        screening_filter_form = None

    return render(
        request,
        "awards/award.html",
        {
            "event": event,
            "other_events": other_events,
            "recommendations_by_category": recommendations_by_category,
            "nominations_by_category": nominations_by_category,
            "can_view_reports": event.user_can_view_reports(request.user),
            "can_access_screening": can_access_screening,
            "screened_by_me_count": screened_by_me_count,
            "screening_filter_form": screening_filter_form,
            # Normally, recommendations will be shown until the nominations are posted, even if the
            # recommendation period closes before then (in which case the recommendations will be
            # shown but "locked-in"). However, an event might leave recommendations open even after
            # nominations are posted (e.g. because they're using the recommendations as public voting
            # on the final winner), in which case we should (obviously) show them.
            "showing_recommendations": event.recommendations_enabled or not nominations_by_category,
            "can_remove_recommendations": event.recommendations_enabled,
        },
    )


@require_POST
@login_required
@writeable_site_required
def remove_recommendation(request, recommendation_id):
    recommendation = get_object_or_404(
        Recommendation.objects.filter(user=request.user, category__event__recommendations_enabled=True),
        id=recommendation_id,
    )

    recommendation.delete()
    return HttpResponseRedirect(reverse("award", args=(recommendation.category.event.slug,)))


@login_required
def report(request, event_slug, category_id):
    event = get_object_or_404(Event.objects.filter(reporting_enabled=True), slug=event_slug)
    category = get_object_or_404(event.categories.all(), id=category_id)
    if not event.user_can_view_reports(request.user):
        raise PermissionDenied

    productions = category.get_recommendation_report().prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser"
    )

    return render(
        request,
        "awards/report.html",
        {
            "event": event,
            "category": category,
            "productions": productions,
        },
    )


def candidates(request, event_slug, category_slug):
    event = get_object_or_404(Event.objects.filter(recommendations_enabled=True), slug=event_slug)
    category = get_object_or_404(event.categories.all(), slug=category_slug)

    productions = (
        category.eligible_productions()
        .prefetch_related(
            "author_nicks__releaser",
            "author_affiliation_nicks__releaser",
            "types",
            "platforms",
        )
        .order_by("sortable_title")
    )

    production_page = get_page(productions, request.GET.get("page", "1"))

    return render(
        request,
        "awards/candidates.html",
        {
            "event": event,
            "category": category,
            "production_page": production_page,
            "pagination_controls": PaginationControls(
                production_page, reverse("awards_candidates", args=[event_slug, category_slug])
            ),
        },
    )


def screening(request, event_slug):
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    # filter_options_by_event=False ensures that if (for example) a platform with no
    # screenable productions is selected (which would mean that it wouldn't have been
    # presented as an option in the first place), the filter will do the sensible thing
    # (reporting no results) rather than rejecting the form as invalid.
    filter_form = ScreeningFilterForm(event, request.GET, filter_options_by_event=False)
    form_for_display = ScreeningFilterForm(event, request.GET, filter_options_by_event=True)

    base_url = reverse("awards_screening", args=[event.slug])
    query_string = filter_form.as_query_string()
    screening_url = f"{base_url}?{query_string}" if query_string else base_url

    if request.method == "POST":
        production_id = request.POST.get("production_id")
        is_accepted = request.POST.get("accept") == "yes"

        try:
            production = event.screenable_productions().get(id=production_id)
        except Production.DoesNotExist:
            return HttpResponseRedirect(screening_url)

        event.screening_decisions.update_or_create(
            user=request.user,
            production=production,
            defaults={"is_accepted": is_accepted},
        )

        messages.success(request, f"Given a '{'Yay' if is_accepted else 'Nay'}' to {production.title}.")
        return HttpResponseRedirect(screening_url)

    else:
        already_screened_production_ids = event.screening_decisions.filter(user=request.user).values_list(
            "production_id", flat=True
        )
        productions_matching_criteria = filter_form.filter(event.screenable_productions())
        unscreened_productions_matching_criteria = productions_matching_criteria.exclude(
            id__in=already_screened_production_ids
        )

        production = unscreened_productions_matching_criteria.order_by("?").first()
        if not production:
            if productions_matching_criteria.exists():
                messages.success(request, "You have screened all productions that fit the chosen criteria. Yay!")
            else:
                messages.error(request, "There are no productions that fit the chosen criteria.")
            return_url = f'{reverse("award", args=(event.slug,))}?{query_string}'
            return HttpResponseRedirect(return_url)

        comment_form = ScreeningCommentForm()
        comment_url = reverse("awards_screening_comment", args=[event.slug, production.id])
        comment_url = f"{comment_url}?{query_string}" if query_string else comment_url

        comments = event.screening_comments.filter(production=production).order_by("created_at").select_related("user")

        return render(
            request,
            "awards/screening.html",
            {
                "event": event,
                "production": production,
                "result_count": unscreened_productions_matching_criteria.count(),
                "carousel": Carousel(production, AnonymousUser()),
                "downloads_panel": DownloadsPanel(production, AnonymousUser()),
                "screening_url": screening_url,
                "filter_form": form_for_display,
                "comment_form": comment_form,
                "comment_url": comment_url,
                "comments": comments,
            },
        )


def screening_production(request, event_slug, production_id):
    """Access the screening page for a specific production."""
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    filter_form = ScreeningFilterForm(event, request.GET, filter_options_by_event=False)
    base_url = reverse("awards_screening", args=[event.slug])
    query_string = filter_form.as_query_string()
    screening_url = f"{base_url}?{query_string}" if query_string else base_url

    production = get_object_or_404(event.screenable_productions(), id=production_id)
    comment_form = ScreeningCommentForm()
    comment_url = reverse("awards_screening_comment", args=[event.slug, production.id])
    comment_url = f"{comment_url}?{query_string}" if query_string else comment_url

    comments = event.screening_comments.filter(production=production).order_by("created_at").select_related("user")

    return render(
        request,
        "awards/screening.html",
        {
            "event": event,
            "production": production,
            "carousel": Carousel(production, AnonymousUser()),
            "downloads_panel": DownloadsPanel(production, AnonymousUser()),
            "screening_url": screening_url,
            "comment_form": comment_form,
            "comment_url": comment_url,
            "comments": comments,
        },
    )


@require_POST
def screening_comment(request, event_slug, production_id):
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    production = get_object_or_404(event.screenable_productions(), id=production_id)
    comment = ScreeningComment(production=production, event=event, user=request.user)
    comment_form = ScreeningCommentForm(request.POST, instance=comment)

    filter_form = ScreeningFilterForm(event, request.GET, filter_options_by_event=False)
    return_url = reverse("awards_screening_production", args=[event.slug, production_id])
    query_string = filter_form.as_query_string()
    return_url = f"{return_url}?{query_string}" if query_string else return_url

    if comment_form.is_valid():
        comment_form.save()

    return HttpResponseRedirect(return_url)


def screening_review(request, event_slug):
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    decisions = (
        event.screening_decisions.filter(user=request.user)
        .select_related("production")
        .prefetch_related(
            "production__author_nicks__releaser",
            "production__author_affiliation_nicks__releaser",
            "production__platforms",
            "production__types",
        )
        .order_by("-created_at")
    )
    decision_choice = request.GET.get("decision")
    if decision_choice:
        decisions = decisions.filter(is_accepted=(decision_choice == "yay"))

    decision_page = get_page(decisions, request.GET.get("page", "1"))

    screenshots = Screenshot.select_for_production_ids([decision.production_id for decision in decision_page])

    rows = [(decision, decision.production, screenshots.get(decision.production_id)) for decision in decision_page]

    return render(
        request,
        "awards/screening_review.html",
        {
            "event": event,
            "rows": rows,
            "pagination_controls": PaginationControls(
                decision_page, reverse("awards_screening_review", args=[event.slug])
            ),
            "decision_choice": decision_choice,
        },
    )


@require_POST
def screening_review_change(request, event_slug, decision_id):
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    decision = get_object_or_404(event.screening_decisions, id=decision_id, user=request.user)

    new_decision = request.POST.get("decision")
    if new_decision == "skip":
        decision.delete()
    else:
        decision.is_accepted = new_decision == "yay"
        decision.save()

    redirect_url = reverse("awards_screening_review", args=[event.slug])
    if request.GET.get("page"):
        redirect_url += f"?page={request.GET['page']}"

    return HttpResponseRedirect(redirect_url)


def screening_report(request, event_slug):
    event = get_object_or_404(Event.objects.filter(screening_enabled=True), slug=event_slug)

    if not event.user_can_access_screening(request.user):
        raise PermissionDenied

    # filter_options_by_event=False ensures that if (for example) a platform with no
    # screenable productions is selected (which would mean that it wouldn't have been
    # presented as an option in the first place), the filter will do the sensible thing
    # (reporting no results) rather than rejecting the form as invalid.
    filter_form = ScreeningFilterForm(event, request.GET, filter_options_by_event=False)

    productions = (
        filter_form.filter(event.screenable_productions())
        .order_by("sortable_title")
        .prefetch_related(
            "author_nicks__releaser",
            "author_affiliation_nicks__releaser",
            "types",
            "platforms",
        )
    )

    if request.GET.get("format") == "csv":
        # Export CSV
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{event.slug}_screening_report.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Title",
                "By",
                "Demozoo URL",
                "Type",
                "Platform",
                "Yay",
                "Nay",
            ]
        )
        for production in productions:
            platforms = ", ".join(platform.name for platform in production.platforms.all())
            types = ", ".join(pt.name for pt in production.types.all())

            writer.writerow(
                [
                    production.title,
                    production.byline_string,
                    "https://demozoo.org" + production.get_absolute_url(),
                    types,
                    platforms,
                    production.yay_count,
                    production.nay_count,
                ]
            )

        return response

    else:
        production_page = get_page(productions, request.GET.get("page", "1"))
        form_for_display = ScreeningFilterForm(event, request.GET, filter_options_by_event=True)
        export_url_params = filter_form.as_query_dict()
        export_url_params.setlist("format", ["csv"])
        export_url = f"{reverse('awards_screening_report', args=[event.slug])}?{export_url_params.urlencode()}"

        return render(
            request,
            "awards/screening_report.html",
            {
                "event": event,
                "productions": production_page,
                "production_count": productions.count(),
                "pagination_controls": PaginationControls(
                    production_page,
                    reverse("awards_screening_report", args=[event.slug]),
                    query_dict=filter_form.as_query_dict(),
                ),
                "filter_form": form_for_display,
                "export_url": export_url,
            },
        )
