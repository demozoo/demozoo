from django.conf.urls import url

from productions.views import productions as production_views
from productions.views import music as music_views
from productions.views import graphics as graphic_views

urlpatterns = [
    url(r'^productions/$', production_views.index, {}, 'productions'),
    url(r'^productions/(\d+)/$', production_views.show, {}, 'production'),
    url(r'^productions/(\d+)/history/$', production_views.history, {}, 'production_history'),
    url(r'^productions/(\d+)/carousel/$', production_views.carousel, {}, 'production_carousel'),

    url(r'^music/$', music_views.index, {}, 'musics'),
    url(r'^music/(\d+)/$', music_views.show, {}, 'music'),
    url(r'^music/(\d+)/edit_core_details/$', production_views.edit_core_details, {}, 'music_edit_core_details'),
    url(r'^music/new/$', music_views.create, {}, 'new_music'),
    url(r'^music/(\d+)/history/$', music_views.history, {}, 'music_history'),

    url(r'^graphics/$', graphic_views.index, {}, 'graphics'),
    url(r'^graphics/(\d+)/$', graphic_views.show, {}, 'graphic'),
    url(r'^graphics/(\d+)/edit_core_details/$', production_views.edit_core_details, {}, 'graphics_edit_core_details'),
    url(r'^graphics/new/$', graphic_views.create, {}, 'new_graphics'),
    url(r'^graphics/(\d+)/history/$', graphic_views.history, {}, 'graphics_history'),

    url(r'^productions/new/$', production_views.create, {}, 'new_production'),
    url(r'^productions/autocomplete/$', production_views.autocomplete, {}),
    url(r'^productions/autocomplete_tags/$', production_views.autocomplete_tags, {}),
    url(r'^productions/tagged/(.+)/$', production_views.tagged, {}, 'productions_tagged'),
    url(r'^productions/(\d+)/edit_core_details/$', production_views.edit_core_details, {}, 'production_edit_core_details'),
    url(r'^productions/(\d+)/add_credit/$', production_views.add_credit, {}, 'production_add_credit'),
    url(r'^productions/(\d+)/edit_credit/(\d+)/$', production_views.edit_credit, {}, 'production_edit_credit'),
    url(r'^productions/(\d+)/delete_credit/(\d+)/$', production_views.delete_credit, {}, 'production_delete_credit'),
    url(r'^productions/(\d+)/edit_notes/$', production_views.edit_notes, {}, 'production_edit_notes'),
    url(r'^productions/(\d+)/edit_external_links/$', production_views.edit_external_links, {}, 'production_edit_external_links'),
    url(r'^productions/(\d+)/edit_download_links/$', production_views.edit_download_links, {}, 'production_edit_download_links'),
    url(r'^productions/(\d+)/add_screenshot/$', production_views.add_screenshot, {}, 'production_add_screenshot'),
    url(r'^productions/(\d+)/add_artwork/$', production_views.add_screenshot, {'is_artwork_view': True}, 'production_add_artwork'),
    url(r'^productions/(\d+)/screenshots/$', production_views.screenshots, {}, 'production_screenshots'),
    url(r'^productions/(\d+)/artwork/$', production_views.artwork, {}, 'production_artwork'),
    url(r'^productions/(\d+)/screenshots/edit/$', production_views.edit_screenshots, {}, 'production_edit_screenshots'),
    url(r'^productions/(\d+)/artwork/edit/$', production_views.edit_artwork, {}, 'production_edit_artwork'),
    url(r'^productions/(\d+)/delete_screenshot/(\d+)/$', production_views.delete_screenshot, {}, 'production_delete_screenshot'),
    url(r'^productions/(\d+)/delete_artwork/(\d+)/$', production_views.delete_screenshot, {'is_artwork_view': True}, 'production_delete_artwork'),
    url(r'^productions/(\d+)/edit_soundtracks/$', production_views.edit_soundtracks, {}, 'production_edit_soundtracks'),
    url(r'^productions/(\d+)/edit_pack_contents/$', production_views.edit_pack_contents, {}, 'production_edit_pack_contents'),
    url(r'^productions/(\d+)/edit_tags/$', production_views.edit_tags, {}, 'production_edit_tags'),
    url(r'^productions/(\d+)/add_tag/$', production_views.add_tag, {}, 'production_add_tag'),
    url(r'^productions/(\d+)/remove_tag/$', production_views.remove_tag, {}, 'production_remove_tag'),
    url(r'^productions/(\d+)/delete/$', production_views.delete, {}, 'delete_production'),
    url(r'^productions/(\d+)/add_blurb/$', production_views.add_blurb, {}, 'production_add_blurb'),
    url(r'^productions/(\d+)/edit_blurb/(\d+)/$', production_views.edit_blurb, {}, 'production_edit_blurb'),
    url(r'^productions/(\d+)/delete_blurb/(\d+)/$', production_views.delete_blurb, {}, 'production_delete_blurb'),
    url(r'^productions/(\d+)/edit_info/$', production_views.edit_info_files, {}, 'production_edit_info_files'),
    url(r'^productions/(\d+)/info/(\d+)/$', production_views.info_file, {}, 'production_info_file'),
    url(r'^productions/(\d+)/lock/$', production_views.lock, {}, 'lock_production'),
    url(r'^productions/(\d+)/protected/$', production_views.protected, {}, 'production_protected'),
]
