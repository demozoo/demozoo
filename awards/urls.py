from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from awards.views import recommend, remove_recommendation, report, user_recommendations


urlpatterns = [
    url(r'^([\w\-]+)/recommend/(\d+)/$', recommend, {}, 'awards_recommend'),
    url(r'^([\w\-]+)/$', user_recommendations, {}, 'awards_user_recommendations'),
    url(r'^remove_recommendation/(\d+)/$', remove_recommendation, {}, 'awards_remove_recommendation'),
    url(r'^([\w\-]+)/report/(\d+)/$', report, {}, 'awards_report'),
]
