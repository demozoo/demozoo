from django.urls import re_path

from awards.views import candidates, recommend, remove_recommendation, report, show


urlpatterns = [
    re_path(r"^([\w\-]+)/recommend/(\d+)/$", recommend, {}, "awards_recommend"),
    re_path(r"^([\w\-]+)/$", show, {}, "award"),
    re_path(r"^remove_recommendation/(\d+)/$", remove_recommendation, {}, "awards_remove_recommendation"),
    re_path(r"^([\w\-]+)/report/(\d+)/$", report, {}, "awards_report"),
    re_path(r"^([\w\-]+)/([\w\-]+)/$", candidates, {}, "awards_candidates"),
]
