from django.conf.urls import re_path

from maintenance import views


app_name = 'maintenance'

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^fix_release_dates$', views.fix_release_dates, name='fix_release_dates'),
    re_path(r'^add_membership$', views.add_membership, name='add_membership'),
    re_path(r'^add_sceneorg_link_to_party$', views.add_sceneorg_link_to_party, name='add_sceneorg_link_to_party'),
    re_path(
        r'^result_file_encoding/(\d+)/$', views.FixResultsFileEncodingView.as_view(),
        name='fix_results_file_encoding'
    ),
    re_path(
        r'^prod_info_file_encoding/(\d+)/$', views.FixProdInfoFileEncodingView.as_view(),
        name='fix_prod_info_file_encoding'
    ),
    re_path(
        r'^bbs_text_ad_encoding/(\d+)/$', views.FixBBSTextAdEncodingView.as_view(),
        name='fix_bbs_text_ad_encoding'
    ),
    re_path(r'^exclude$', views.exclude, name='exclude'),
    re_path(r'^archive_member/(\d+)/$', views.view_archive_member, name='view_archive_member'),
    re_path(r'^resolve_screenshot/(\d+)/(\d+)/$', views.resolve_screenshot, name='resolve_screenshot'),

    re_path(
        r'^janeway_unique_author_name_matches/same/(\d+)/(\d+)/$', views.janeway_authors_same,
        name='janeway_authors_same'
    ),
    re_path(
        r'^janeway_unique_author_name_matches/different/(\d+)/(\d+)/$', views.janeway_authors_different,
        name='janeway_authors_different'
    ),
    re_path(
        r'^janeway_unique_author_name_matches/detail/(\d+)/(\d+)/$', views.janeway_authors_detail,
        name='janeway_authors_detail'
    ),
]

for section_title, reports in views.reports:
    urlpatterns.extend([
        report.get_urlpattern() for report in reports if hasattr(report, 'get_urlpattern')
    ])
