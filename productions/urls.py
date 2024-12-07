from django.urls import re_path

from productions.views import graphics as graphic_views
from productions.views import music as music_views
from productions.views import productions as production_views


urlpatterns = [
    re_path(r"^productions/$", production_views.ProductionIndexView.as_view(), {}, "productions"),
    re_path(r"^productions/(\d+)/$", production_views.ProductionShowView.as_view(), {}, "production"),
    re_path(
        r"^productions/(\d+)/history/$", production_views.ProductionHistoryView.as_view(), {}, "production_history"
    ),
    re_path(r"^productions/(\d+)/carousel/$", production_views.carousel, {}, "production_carousel"),
    re_path(r"^music/$", music_views.MusicIndexView.as_view(), {}, "musics"),
    re_path(r"^music/(\d+)/$", music_views.MusicShowView.as_view(), {}, "music"),
    re_path(r"^music/(\d+)/edit_core_details/$", production_views.edit_core_details, {}, "music_edit_core_details"),
    re_path(r"^music/new/$", music_views.CreateMusicView.as_view(), {}, "new_music"),
    re_path(r"^music/(\d+)/history/$", music_views.MusicHistoryView.as_view(), {}, "music_history"),
    re_path(r"^graphics/$", graphic_views.GraphicsIndexView.as_view(), {}, "graphics"),
    re_path(r"^graphics/(\d+)/$", graphic_views.GraphicsShowView.as_view(), {}, "graphic"),
    re_path(
        r"^graphics/(\d+)/edit_core_details/$", production_views.edit_core_details, {}, "graphics_edit_core_details"
    ),
    re_path(r"^graphics/new/$", graphic_views.CreateGraphicsView.as_view(), {}, "new_graphics"),
    re_path(r"^graphics/(\d+)/history/$", graphic_views.GraphicsHistoryView.as_view(), {}, "graphics_history"),
    re_path(r"^productions/new/$", production_views.CreateProductionView.as_view(), {}, "new_production"),
    re_path(r"^productions/autocomplete/$", production_views.autocomplete, {}),
    re_path(r"^productions/autocomplete_tags/$", production_views.autocomplete_tags, {}),
    re_path(r"^productions/tagged/([^\/]+)/$", production_views.tagged, {}, "productions_tagged"),
    re_path(
        r"^productions/(\d+)/edit_core_details/$",
        production_views.edit_core_details,
        {},
        "production_edit_core_details",
    ),
    re_path(r"^productions/(\d+)/add_credit/$", production_views.add_credit, {}, "production_add_credit"),
    re_path(r"^productions/(\d+)/edit_credit/(\d+)/$", production_views.edit_credit, {}, "production_edit_credit"),
    re_path(
        r"^productions/(\d+)/delete_credit/(\d+)/$", production_views.delete_credit, {}, "production_delete_credit"
    ),
    re_path(r"^productions/(\d+)/edit_notes/$", production_views.edit_notes, {}, "production_edit_notes"),
    re_path(
        r"^productions/(\d+)/edit_external_links/$",
        production_views.edit_external_links,
        {},
        "production_edit_external_links",
    ),
    re_path(
        r"^productions/(\d+)/edit_download_links/$",
        production_views.edit_download_links,
        {},
        "production_edit_download_links",
    ),
    re_path(r"^productions/(\d+)/add_screenshot/$", production_views.add_screenshot, {}, "production_add_screenshot"),
    re_path(
        r"^productions/(\d+)/add_artwork/$",
        production_views.add_screenshot,
        {"is_artwork_view": True},
        "production_add_artwork",
    ),
    re_path(r"^productions/(\d+)/screenshots/$", production_views.screenshots, {}, "production_screenshots"),
    re_path(r"^productions/(\d+)/artwork/$", production_views.artwork, {}, "production_artwork"),
    re_path(
        r"^productions/(\d+)/screenshots/edit/$", production_views.edit_screenshots, {}, "production_edit_screenshots"
    ),
    re_path(r"^productions/(\d+)/artwork/edit/$", production_views.edit_artwork, {}, "production_edit_artwork"),
    re_path(
        r"^productions/(\d+)/delete_screenshot/(\d+)/$",
        production_views.DeleteScreenshotView.as_view(),
        {},
        "production_delete_screenshot",
    ),
    re_path(
        r"^productions/(\d+)/delete_artwork/(\d+)/$",
        production_views.DeleteArtworkView.as_view(),
        {},
        "production_delete_artwork",
    ),
    re_path(
        r"^productions/(\d+)/edit_soundtracks/$", production_views.edit_soundtracks, {}, "production_edit_soundtracks"
    ),
    re_path(
        r"^productions/(\d+)/edit_pack_contents/$",
        production_views.edit_pack_contents,
        {},
        "production_edit_pack_contents",
    ),
    re_path(
        r"^productions/(\d+)/edit_tags/$", production_views.ProductionEditTagsView.as_view(), {}, "production_edit_tags"
    ),
    re_path(r"^productions/(\d+)/add_tag/$", production_views.ProductionAddTagView.as_view(), {}, "production_add_tag"),
    re_path(
        r"^productions/(\d+)/remove_tag/$",
        production_views.ProductionRemoveTagView.as_view(),
        {},
        "production_remove_tag",
    ),
    re_path(r"^productions/(\d+)/delete/$", production_views.DeleteProductionView.as_view(), {}, "delete_production"),
    re_path(r"^productions/(\d+)/add_blurb/$", production_views.add_blurb, {}, "production_add_blurb"),
    re_path(r"^productions/(\d+)/edit_blurb/(\d+)/$", production_views.edit_blurb, {}, "production_edit_blurb"),
    re_path(
        r"^productions/(\d+)/delete_blurb/(\d+)/$",
        production_views.DeleteBlurbView.as_view(),
        {},
        "production_delete_blurb",
    ),
    re_path(
        r"^productions/(\d+)/edit_info/$",
        production_views.EditInfoFilesView.as_view(),
        {},
        "production_edit_info_files",
    ),
    re_path(r"^productions/(\d+)/info/(\d+)/$", production_views.info_file, {}, "production_info_file"),
    re_path(r"^productions/(\d+)/lock/$", production_views.LockProductionView.as_view(), {}, "lock_production"),
    re_path(r"^productions/(\d+)/protected/$", production_views.protected, {}, "production_protected"),
]
