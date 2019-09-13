from django.conf.urls import url

from maintenance import views

app_name = 'maintenance'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^fix_release_dates$', views.fix_release_dates, name='fix_release_dates'),
    url(r'^add_membership$', views.add_membership, name='add_membership'),
    url(r'^add_sceneorg_link_to_party$', views.add_sceneorg_link_to_party, name='add_sceneorg_link_to_party'),
    url(r'^result_file_encoding/(\d+)/$', views.fix_results_file_encoding, name='fix_results_file_encoding'),
    url(r'^exclude$', views.exclude, name='exclude'),
    url(r'^archive_member/(\d+)/$', views.view_archive_member, name='view_archive_member'),
    url(r'^resolve_screenshot/(\d+)/(\d+)/$', views.resolve_screenshot, name='resolve_screenshot'),

    url(r'^janeway_unique_author_name_matches/same/(\d+)/(\d+)/$', views.janeway_authors_same, name='janeway_authors_same'),
    url(r'^janeway_unique_author_name_matches/different/(\d+)/(\d+)/$', views.janeway_authors_different, name='janeway_authors_different'),
    url(r'^janeway_unique_author_name_matches/detail/(\d+)/(\d+)/$', views.janeway_authors_detail, name='janeway_authors_detail'),
]

for section_title, reports in views.reports:
    urlpatterns.extend([
        report.get_urlpattern() for report in reports if hasattr(report, 'get_urlpattern')
    ])
