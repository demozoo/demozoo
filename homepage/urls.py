from django.urls import re_path

from homepage.views import activity as activity_views
from homepage.views import banners as banner_views
from homepage.views import diagnostics as diagnostics_views
from homepage.views import home as home_views
from homepage.views import news as news_views


urlpatterns = [
    re_path(r"^$", home_views.home, {}, "home"),
    re_path(r"^news/$", news_views.news, {}, "news"),
    re_path(r"^news/(\d+)/$", news_views.news_story, {}, "news_story"),
    re_path(r"^news/new/$", news_views.add_news, {}, "add_news"),
    re_path(r"^news/(\d+)/edit/$", news_views.edit_news, {}, "edit_news"),
    re_path(r"^news/(\d+)/delete/$", news_views.DeleteNewsStoryView.as_view(), {}, "delete_news"),
    re_path(r"^news/browse_images/$", news_views.browse_images, {}, "news_images_browse"),
    re_path(r"^banners/$", banner_views.index, {}, "banners_index"),
    re_path(r"^banners/new/$", banner_views.add_banner, {}, "add_banner"),
    re_path(r"^banners/(\d+)/edit/$", banner_views.edit_banner, {}, "edit_banner"),
    re_path(r"^banners/(\d+)/delete/$", banner_views.DeleteBannerView.as_view(), {}, "delete_banner"),
    re_path(r"^banners/browse_images/$", banner_views.browse_images, {}, "banner_images_browse"),
    re_path(r"^latest_activity/$", activity_views.latest_activity, {}, "latest_activity"),
    re_path(r"^edits/$", activity_views.recent_edits, {}, "recent_edits"),
    re_path(r"^error/$", diagnostics_views.error_test, {}, "error_test"),
    re_path(r"^404/$", diagnostics_views.page_not_found_test, {}, "page_not_found_test"),
]
