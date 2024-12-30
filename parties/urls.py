from django.urls import path
from django.views.generic.base import RedirectView

from parties.views import competition_api as competition_api_views
from parties.views import competitions as competition_views
from parties.views import parties as party_views


urlpatterns = [
    path("parties/", party_views.by_date, {}, "parties"),
    path("parties/year/", RedirectView.as_view(url="/parties/")),
    path("parties/year/<int:year>/", party_views.by_date, {}, "parties_year"),
    path("parties/by_name/", party_views.by_name, {}, "parties_by_name"),
    path("parties/by_date/", RedirectView.as_view(url="/parties/"), name="parties_by_date"),
    path("parties/<int:party_id>/", party_views.show, {}, "party"),
    path("parties/<int:party_id>/history/", party_views.history, {}, "party_history"),
    path("parties/series/<int:party_series_id>/", party_views.show_series, {}, "party_series"),
    path("parties/series/<int:party_series_id>/history/", party_views.series_history, {}, "party_series_history"),
    path("parties/series/<int:party_series_id>/edit/", party_views.EditSeriesView.as_view(), {}, "party_edit_series"),
    path(
        "parties/series/<int:party_series_id>/edit_notes/",
        party_views.EditSeriesNotesView.as_view(),
        {},
        "party_edit_series_notes",
    ),
    path(
        "parties/series/<int:party_series_id>/edit_external_links/",
        party_views.EditSeriesExternalLinksView.as_view(),
        {},
        "party_edit_series_external_links",
    ),
    path("parties/new/", party_views.CreateView.as_view(), {}, "new_party"),
    path(
        "parties/<int:party_id>/add_competition/", party_views.AddCompetitionView.as_view(), {}, "party_add_competition"
    ),
    path("parties/<int:party_id>/edit/", party_views.EditView.as_view(), {}, "edit_party"),
    path(
        "parties/<int:party_id>/edit_competition/<int:competition_id>/",
        party_views.edit_competition,
        {},
        "party_edit_competition",
    ),
    path("parties/<int:party_id>/edit_notes/", party_views.EditNotesView.as_view(), {}, "party_edit_notes"),
    path(
        "parties/<int:party_id>/edit_external_links/",
        party_views.EditExternalLinksView.as_view(),
        {},
        "party_edit_external_links",
    ),
    path("parties/<int:party_id>/results_file/<int:file_id>/", party_views.results_file, {}, "party_results_file"),
    path("parties/autocomplete/", party_views.autocomplete, {}),
    path(
        "parties/<int:party_id>/edit_invitations/",
        party_views.EditInvitationsView.as_view(),
        {},
        "party_edit_invitations",
    ),
    path("parties/<int:party_id>/edit_releases/", party_views.EditReleasesView.as_view(), {}, "party_edit_releases"),
    path(
        "parties/<int:party_id>/edit_share_image/",
        party_views.EditShareImageView.as_view(),
        {},
        "party_edit_share_image",
    ),
    path("parties/<int:party_id>/add_organiser/", party_views.AddOrganiserView.as_view(), {}, "party_add_organiser"),
    path(
        "parties/<int:party_id>/edit_organiser/<int:organiser_id>/",
        party_views.EditOrganiserView.as_view(),
        {},
        "party_edit_organiser",
    ),
    path(
        "parties/<int:party_id>/remove_organiser/<int:organiser_id>/",
        party_views.RemoveOrganiserView.as_view(),
        {},
        "party_remove_organiser",
    ),
    path("competitions/<int:competition_id>/", competition_views.show, {}, "competition"),
    path("competitions/<int:competition_id>/history/", competition_views.history, {}, "competition_history"),
    path("competitions/<int:competition_id>/edit/", competition_views.edit, {}, "competition_edit"),
    path(
        "competitions/<int:competition_id>/import_text/", competition_views.import_text, {}, "competition_import_text"
    ),
    path(
        "competitions/<int:competition_id>/delete/",
        competition_views.DeleteCompetitionView.as_view(),
        {},
        "delete_competition",
    ),
    path("competition_api/add_placing/<int:competition_id>/", competition_api_views.add_placing, {}),
    path("competition_api/update_placing/<int:placing_id>/", competition_api_views.update_placing, {}),
    path("competition_api/delete_placing/<int:placing_id>/", competition_api_views.delete_placing, {}),
    path("parties/ical_info/", party_views.ical_feed_url, {}, "ical_feed_url"),
    path("parties/demozoo_ical_feed/", party_views.ical_feed, {}, "ical_feed"),
    path("parties/demozoo_historical_ical_feed/", party_views.historical_ical_feed, {}, "historical_ical_feed"),
    path("parties/demozoo_online_only_ical_feed/", party_views.online_ical_feed, {}, "online_only_ical_feed"),
    path("parties/demozoo_country_ical_feed/<str:code>", party_views.country_ical_feed, {}, "country_ical_feed"),
]
