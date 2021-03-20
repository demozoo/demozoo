from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from homepage.views import banners as banner_views
from homepage.views import home as home_views
from homepage.views import news as news_views


urlpatterns = [
    url(r'^$', home_views.home, {}, 'home'),

    url(r'^news/new/$', news_views.add_news, {}, 'add_news'),
    url(r'^news/(\d+)/edit/$', news_views.edit_news, {}, 'edit_news'),
    url(r'^news/(\d+)/delete/$', news_views.delete_news, {}, 'delete_news'),
    url(r'^news/browse_images/$', news_views.browse_images, {}, 'news_images_browse'),

    url(r'^banners/$', banner_views.index, {}, 'banners_index'),
    url(r'^banners/new/$', banner_views.add_banner, {}, 'add_banner'),
    url(r'^banners/(\d+)/edit/$', banner_views.edit_banner, {}, 'edit_banner'),
    url(r'^banners/(\d+)/delete/$', banner_views.delete_banner, {}, 'delete_banner'),
    url(r'^banners/browse_images/$', banner_views.browse_images, {}, 'banner_images_browse'),
]
