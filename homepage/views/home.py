import datetime

from django.shortcuts import render

from comments.models import Comment
from forums.models import Topic
from homepage.models import Banner, NewsStory
from parties.models import Party
from productions.models import Production, Screenshot


def home(request):
    if request.user.is_authenticated:
        banner = (
            Banner.objects.filter(show_for_logged_in_users=True)
            .order_by("-created_at")
            .select_related("banner_image")
            .first()
        )
    else:
        banner = (
            Banner.objects.filter(show_for_anonymous_users=True)
            .order_by("-created_at")
            .select_related("banner_image")
            .first()
        )

    latest_releases = (
        Production.objects.filter(has_screenshot=True, release_date_date__isnull=False)
        .exclude(tags__slug__in=["xxx", "nsfw"])
        .only(
            "id",
            "title",
            "release_date_date",
            "release_date_precision",
            "supertype",
        )
        .prefetch_related("author_nicks", "author_affiliation_nicks", "platforms", "types")
        .order_by("-release_date_date", "-created_at")[:5]
    )
    latest_releases_screenshots = Screenshot.select_for_production_ids([prod.id for prod in latest_releases])
    latest_releases_and_screenshots = [
        (production, latest_releases_screenshots.get(production.id)) for production in latest_releases
    ]

    one_year_ago = datetime.datetime.now() - datetime.timedelta(365)
    latest_additions = (
        Production.objects.exclude(release_date_date__gte=one_year_ago)
        .prefetch_related("author_nicks", "author_affiliation_nicks", "platforms", "types")
        .order_by("-created_at")[:5]
    )

    comments = Comment.objects.select_related("user").prefetch_related("commentable").order_by("-created_at")[:5]

    today = datetime.date.today()
    if today.day > 15:
        start_date = today.replace(day=1)
    else:
        try:
            start_date = today.replace(day=1, month=today.month - 1)
        except ValueError:
            start_date = today.replace(day=1, month=12, year=today.year - 1)

    try:
        end_date = today.replace(day=1, month=today.month + 3)
    except ValueError:
        end_date = today.replace(day=1, month=today.month - 9, year=today.year + 1)

    parties = (
        Party.objects.filter(start_date_date__gte=start_date, start_date_date__lt=end_date)
        .exclude(start_date_precision="y")
        .order_by("start_date_date")
    )

    if request.user.is_staff:
        news_stories = NewsStory.objects.select_related("image").order_by("-created_at")[:6]
    else:
        news_stories = NewsStory.objects.filter(is_public=True).select_related("image").order_by("-created_at")[:6]

    return render(
        request,
        "homepage/home.html",
        {
            "banner": banner,
            "news_stories": news_stories,
            "forum_topics": (
                Topic.objects.filter(residue=False)
                .order_by("-last_post_at")
                .select_related("created_by_user", "last_post_by_user")[:5]
            ),
            "latest_releases_and_screenshots": latest_releases_and_screenshots,
            "latest_additions": latest_additions,
            "comments": comments,
            "parties": parties,
        },
    )
