from django.urls import re_path
from django.views.generic.base import RedirectView

from parties.views import competition_api as competition_api_views
from parties.views import competitions as competition_views
from parties.views import parties as party_views


urlpatterns = [
    re_path(r'^parties/$', party_views.by_date, {}, 'parties'),
    re_path(r'^parties/year/$', RedirectView.as_view(url='/parties/')),
    re_path(r'^parties/year/(?P<year>\d+)/$', party_views.by_date, {}, 'parties_year'),
    re_path(r'^parties/by_name/$', party_views.by_name, {}, 'parties_by_name'),
    re_path(r'^parties/by_date/$', RedirectView.as_view(url='/parties/'), name='parties_by_date'),
    re_path(r'^parties/(\d+)/$', party_views.show, {}, 'party'),
    re_path(r'^parties/(\d+)/history/$', party_views.history, {}, 'party_history'),
    re_path(r'^parties/series/(\d+)/$', party_views.show_series, {}, 'party_series'),
    re_path(r'^parties/series/(\d+)/history/$', party_views.series_history, {}, 'party_series_history'),
    re_path(r'^parties/series/(\d+)/edit/$', party_views.edit_series, {}, 'party_edit_series'),
    re_path(r'^parties/series/(\d+)/edit_notes/$', party_views.edit_series_notes, {}, 'party_edit_series_notes'),
    re_path(r'^parties/series/(\d+)/edit_external_links/$', party_views.edit_series_external_links, {}, 'party_edit_series_external_links'),
    re_path(r'^parties/new/$', party_views.create, {}, 'new_party'),
    re_path(r'^parties/(\d+)/add_competition/$', party_views.add_competition, {}, 'party_add_competition'),
    re_path(r'^parties/(\d+)/edit/$', party_views.edit, {}, 'edit_party'),
    re_path(r'^parties/(\d+)/edit_competition/(\d+)/$', party_views.edit_competition, {}, 'party_edit_competition'),
    re_path(r'^parties/(\d+)/edit_notes/$', party_views.edit_notes, {}, 'party_edit_notes'),
    re_path(r'^parties/(\d+)/edit_external_links/$', party_views.edit_external_links, {}, 'party_edit_external_links'),
    re_path(r'^parties/(\d+)/results_file/(\d+)/$', party_views.results_file, {}, 'party_results_file'),
    re_path(r'^parties/autocomplete/$', party_views.autocomplete, {}),
    re_path(r'^parties/(\d+)/edit_invitations/$', party_views.edit_invitations, {}, 'party_edit_invitations'),
    re_path(r'^parties/(\d+)/edit_releases/$', party_views.edit_releases, {}, 'party_edit_releases'),
    re_path(r'^parties/(\d+)/edit_share_image/$', party_views.edit_share_image, {}, 'party_edit_share_image'),
    re_path(r'^parties/(\d+)/add_organiser/$', party_views.add_organiser, {}, 'party_add_organiser'),
    re_path(r'^parties/(\d+)/edit_organiser/(\d+)/$', party_views.edit_organiser, {}, 'party_edit_organiser'),
    re_path(
        r'^parties/(\d+)/remove_organiser/(\d+)/$', party_views.RemoveOrganiserView.as_view(), {},
        'party_remove_organiser'
    ),

    re_path(r'^competitions/(\d+)/$', competition_views.show, {}, 'competition'),
    re_path(r'^competitions/(\d+)/history/$', competition_views.history, {}, 'competition_history'),
    re_path(r'^competitions/(\d+)/edit$', competition_views.edit, {}, 'competition_edit'),
    re_path(r'^competitions/(\d+)/import_text$', competition_views.import_text, {}, 'competition_import_text'),
    re_path(
        r'^competitions/(\d+)/delete/$', competition_views.DeleteCompetitionView.as_view(), {},
        'delete_competition'
    ),

    re_path(r'^competition_api/add_placing/(\d+)/$', competition_api_views.add_placing, {}),
    re_path(r'^competition_api/update_placing/(\d+)/$', competition_api_views.update_placing, {}),
    re_path(r'^competition_api/delete_placing/(\d+)/$', competition_api_views.delete_placing, {}),
]
