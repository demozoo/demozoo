from django.urls import path

from homepage.views import activity as activity_views
from homepage.views import banners as banner_views
from homepage.views import diagnostics as diagnostics_views
from homepage.views import home as home_views
from homepage.views import news as news_views


urlpatterns = [
    path("", home_views.home, {}, "home"),
    path("news/", news_views.news, {}, "news"),
    path("news/feed/", news_views.NewsFeed(), {}, "news_feed"),
    path("news/<int:news_story_id>/", news_views.news_story, {}, "news_story"),
    path("news/new/", news_views.add_news, {}, "add_news"),
    path("news/<int:news_story_id>/edit/", news_views.edit_news, {}, "edit_news"),
    path("news/<int:news_story_id>/delete/", news_views.DeleteNewsStoryView.as_view(), {}, "delete_news"),
    path("news/browse_images/", news_views.browse_images, {}, "news_images_browse"),
    path("banners/", banner_views.index, {}, "banners_index"),
    path("banners/new/", banner_views.add_banner, {}, "add_banner"),
    path("banners/<int:banner_id>/edit/", banner_views.edit_banner, {}, "edit_banner"),
    path("banners/<int:banner_id>/delete/", banner_views.DeleteBannerView.as_view(), {}, "delete_banner"),
    path("banners/browse_images/", banner_views.browse_images, {}, "banner_images_browse"),
    path("latest_activity/", activity_views.latest_activity, {}, "latest_activity"),
    path("edits/", activity_views.recent_edits, {}, "recent_edits"),
    path("error/", diagnostics_views.error_test, {}, "error_test"),
    path("404/", diagnostics_views.page_not_found_test, {}, "page_not_found_test"),
]
