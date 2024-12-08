from django.urls import path

from maintenance import views


app_name = "maintenance"

urlpatterns = [
    path("", views.index, name="index"),
    path("fix_release_dates/", views.fix_release_dates, name="fix_release_dates"),
    path("add_membership/", views.add_membership, name="add_membership"),
    path("add_sceneorg_link_to_party/", views.add_sceneorg_link_to_party, name="add_sceneorg_link_to_party"),
    path(
        "result_file_encoding/<int:text_file_id>/",
        views.FixResultsFileEncodingView.as_view(),
        name="fix_results_file_encoding",
    ),
    path(
        "prod_info_file_encoding/<int:text_file_id>/",
        views.FixProdInfoFileEncodingView.as_view(),
        name="fix_prod_info_file_encoding",
    ),
    path(
        "bbs_text_ad_encoding/<int:text_file_id>/",
        views.FixBBSTextAdEncodingView.as_view(),
        name="fix_bbs_text_ad_encoding",
    ),
    path("exclude/", views.exclude, name="exclude"),
    path("archive_member/<int:archive_member_id>/", views.view_archive_member, name="view_archive_member"),
    path(
        "resolve_screenshot/<int:productionlink_id>/<int:archive_member_id>/",
        views.resolve_screenshot,
        name="resolve_screenshot",
    ),
    path(
        "janeway_unique_author_name_matches/same/<int:demozoo_id>/<int:janeway_id>/",
        views.janeway_authors_same,
        name="janeway_authors_same",
    ),
    path(
        "janeway_unique_author_name_matches/different/<int:demozoo_id>/<int:janeway_id>/",
        views.janeway_authors_different,
        name="janeway_authors_different",
    ),
    path(
        "janeway_unique_author_name_matches/detail/<int:demozoo_id>/<int:janeway_id>/",
        views.janeway_authors_detail,
        name="janeway_authors_detail",
    ),
]

for section_title, reports in views.reports:
    urlpatterns.extend([report.get_urlpattern() for report in reports if hasattr(report, "get_urlpattern")])
