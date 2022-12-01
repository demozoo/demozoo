from django.urls import re_path

from awards.views import candidates, recommend, remove_recommendation, report, user_recommendations


urlpatterns = [
    re_path(r'^([\w\-]+)/recommend/(\d+)/$', recommend, {}, 'awards_recommend'),
    re_path(r'^([\w\-]+)/$', user_recommendations, {}, 'awards_user_recommendations'),
    re_path(r'^remove_recommendation/(\d+)/$', remove_recommendation, {}, 'awards_remove_recommendation'),
    re_path(r'^([\w\-]+)/report/(\d+)/$', report, {}, 'awards_report'),
    re_path(r'^([\w\-]+)/([\w\-]+)/$', candidates, {}, 'awards_candidates'),
]
