from django.urls import path

from awards.views import (
    candidates,
    recommend,
    remove_recommendation,
    report,
    screening,
    screening_review,
    screening_review_change,
    show,
)


urlpatterns = [
    path("<slug:event_slug>/recommend/<int:production_id>/", recommend, {}, "awards_recommend"),
    path("<slug:event_slug>/", show, {}, "award"),
    path("<slug:event_slug>/screening/", screening, {}, "awards_screening"),
    path("<slug:event_slug>/screening/review/", screening_review, {}, "awards_screening_review"),
    path(
        "<slug:event_slug>/screening/review/<int:decision_id>/",
        screening_review_change,
        {},
        "awards_screening_review_change",
    ),
    path("remove_recommendation/<int:recommendation_id>/", remove_recommendation, {}, "awards_remove_recommendation"),
    path("<slug:event_slug>/report/<int:category_id>/", report, {}, "awards_report"),
    path("<slug:event_slug>/<slug:category_slug>/", candidates, {}, "awards_candidates"),
]
