from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic.base import RedirectView

from parties.views import competition_api as competition_api_views
from parties.views import competitions as competition_views
from parties.views import parties as party_views

urlpatterns = [
    url(r'^parties/$', party_views.by_date, {}, 'parties'),
    url(r'^parties/year/$', RedirectView.as_view(url='/parties/')),
    url(r'^parties/year/(?P<year>\d+)/$', party_views.by_date, {}, 'parties_year'),
    url(r'^parties/by_name/$', party_views.by_name, {}, 'parties_by_name'),
    url(r'^parties/by_date/$', RedirectView.as_view(url='/parties/'), name='parties_by_date'),
    url(r'^parties/(\d+)/$', party_views.show, {}, 'party'),
    url(r'^parties/(\d+)/history/$', party_views.history, {}, 'party_history'),
    url(r'^parties/series/(\d+)/$', party_views.show_series, {}, 'party_series'),
    url(r'^parties/series/(\d+)/history/$', party_views.series_history, {}, 'party_series_history'),
    url(r'^parties/series/(\d+)/edit/$', party_views.edit_series, {}, 'party_edit_series'),
    url(r'^parties/series/(\d+)/edit_notes/$', party_views.edit_series_notes, {}, 'party_edit_series_notes'),
    url(r'^parties/new/$', party_views.create, {}, 'new_party'),
    url(r'^parties/(\d+)/add_competition/$', party_views.add_competition, {}, 'party_add_competition'),
    url(r'^parties/(\d+)/edit/$', party_views.edit, {}, 'edit_party'),
    url(r'^parties/(\d+)/edit_competition/(\d+)/$', party_views.edit_competition, {}, 'party_edit_competition'),
    url(r'^parties/(\d+)/edit_notes/$', party_views.edit_notes, {}, 'party_edit_notes'),
    url(r'^parties/(\d+)/edit_external_links/$', party_views.edit_external_links, {}, 'party_edit_external_links'),
    url(r'^parties/(\d+)/results_file/(\d+)/$', party_views.results_file, {}, 'party_results_file'),
    url(r'^parties/autocomplete/$', party_views.autocomplete, {}),
    url(r'^parties/(\d+)/edit_invitations/$', party_views.edit_invitations, {}, 'party_edit_invitations'),
    url(r'^parties/(\d+)/edit_releases/$', party_views.edit_releases, {}, 'party_edit_releases'),
    url(r'^parties/(\d+)/edit_share_image/$', party_views.edit_share_image, {}, 'party_edit_share_image'),
    url(r'^parties/(\d+)/add_organiser/$', party_views.add_organiser, {}, 'party_add_organiser'),
    url(r'^parties/(\d+)/edit_organiser/(\d+)/$', party_views.edit_organiser, {}, 'party_edit_organiser'),
    url(r'^parties/(\d+)/remove_organiser/(\d+)/$', party_views.remove_organiser, {}, 'party_remove_organiser'),

    url(r'^competitions/(\d+)/$', competition_views.show, {}, 'competition'),
    url(r'^competitions/(\d+)/history/$', competition_views.history, {}, 'competition_history'),
    url(r'^competitions/(\d+)/edit$', competition_views.edit, {}, 'competition_edit'),
    url(r'^competitions/(\d+)/import_text$', competition_views.import_text, {}, 'competition_import_text'),
    url(r'^competitions/(\d+)/delete/$', competition_views.delete, {}, 'delete_competition'),

    url(r'^competition_api/add_placing/(\d+)/$', competition_api_views.add_placing, {}),
    url(r'^competition_api/update_placing/(\d+)/$', competition_api_views.update_placing, {}),
    url(r'^competition_api/delete_placing/(\d+)/$', competition_api_views.delete_placing, {}),
]
