from django.urls import path

from awards.views import candidates, recommend, remove_recommendation, report, screening, show


urlpatterns = [
    path("<slug:event_slug>/recommend/<int:production_id>/", recommend, {}, "awards_recommend"),
    path("<slug:event_slug>/", show, {}, "award"),
    path("<slug:event_slug>/screening/", screening, {}, "awards_screening"),
    path("remove_recommendation/<int:recommendation_id>/", remove_recommendation, {}, "awards_remove_recommendation"),
    path("<slug:event_slug>/report/<int:category_id>/", report, {}, "awards_report"),
    path("<slug:event_slug>/<slug:category_slug>/", candidates, {}, "awards_candidates"),
]
