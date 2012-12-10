from django.conf.urls import *

# Admin backend
from django.contrib import admin
admin.autodiscover()

import djapian
djapian.load_indexes()

urlpatterns = patterns('',
	# Example:
	# (r'^demozoo2/', include('demozoo2.foo.urls')),

	# Uncomment the admin/doc line below and add 'django.contrib.admindocs'
	# to INSTALLED_APPS to enable admin documentation:
	# (r'^admin/doc/', include('django.contrib.admindocs.urls')),

	(r'^admin/', include(admin.site.urls)),

	(r'^account/$', 'demoscene.views.accounts.index', {}, 'account_index'),
	(r'^account/login/$', 'django.contrib.auth.views.login', {}, 'log_in'),
	(r'^account/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'log_out'),
	(r'^account/signup/$', 'demoscene.views.accounts.signup', {}, 'user_signup'),
	(r'^account/preferences/$', 'demoscene.views.accounts.preferences', {}, 'account_preferences'),
	(r'^account/change_password/$', 'demoscene.views.accounts.change_password', {}, 'account_change_password'),
)

urlpatterns += patterns('demoscene.views',
	(r'^$', 'home.home', {}, 'home'),

	(r'^error/$', 'home.error_test', {}, 'error_test'),
	(r'^edits/$', 'home.recent_edits', {}, 'recent_edits'),

	(r'^productions/$', 'productions.index', {'supertype': 'production'}, 'productions'),
	(r'^productions/(\d+)/$', 'productions.show', {}, 'production'),
	(r'^productions/(\d+)/edit/$', 'productions.edit', {}, 'edit_production'),
	(r'^productions/(\d+)/done/$', 'productions.edit_done', {}, 'edit_production_done'),
	(r'^productions/(\d+)/history/$', 'productions.history', {}, 'production_history'),

	(r'^music/$', 'productions.index', {'supertype': 'music'}, 'musics'),
	(r'^music/tagged/(.+)/$', 'productions.tagged', {'supertype': 'music'}, 'music_tagged'),
	(r'^music/(\d+)/$', 'music.show', {}, 'music'),
	(r'^music/(\d+)/edit/$', 'music.edit', {}, 'edit_music'),
	(r'^music/(\d+)/edit_core_details/$', 'productions.edit_core_details', {}, 'music_edit_core_details'),
	(r'^music/(\d+)/done/$', 'productions.edit_done', {}, 'edit_music_done'),
	(r'^music/new/$', 'music.create', {}, 'new_music'),
	(r'^music/(\d+)/history/$', 'music.history', {}, 'music_history'),

	(r'^graphics/$', 'productions.index', {'supertype': 'graphics'}, 'graphics'),
	(r'^graphics/tagged/(.+)/$', 'productions.tagged', {'supertype': 'graphics'}, 'graphics_tagged'),
	(r'^graphics/(\d+)/$', 'graphics.show', {}, 'graphic'),
	(r'^graphics/(\d+)/edit/$', 'graphics.edit', {}, 'edit_graphics'),
	(r'^graphics/(\d+)/edit_core_details/$', 'productions.edit_core_details', {}, 'graphics_edit_core_details'),
	(r'^graphics/(\d+)/done/$', 'productions.edit_done', {}, 'edit_graphics_done'),
	(r'^graphics/new/$', 'graphics.create', {}, 'new_graphics'),
	(r'^graphics/(\d+)/history/$', 'graphics.history', {}, 'graphics_history'),

	(r'^productions/new/$', 'productions.create', {}, 'new_production'),
	(r'^productions/autocomplete/$', 'productions.autocomplete', {}),
	(r'^productions/tagged/(.+)/$', 'productions.tagged', {'supertype': 'production'}, 'productions_tagged'),
	(r'^productions/(\d+)/edit_core_details/$', 'productions.edit_core_details', {}, 'production_edit_core_details'),
	(r'^productions/(\d+)/add_credit/$', 'productions.add_credit', {}, 'production_add_credit'),
	(r'^productions/(\d+)/edit_credit/(\d+)/$', 'productions.edit_credit', {}, 'production_edit_credit'),
	(r'^productions/(\d+)/delete_credit/(\d+)/$', 'productions.delete_credit', {}, 'production_delete_credit'),
	(r'^productions/(\d+)/edit_notes/$', 'productions.edit_notes', {}, 'production_edit_notes'),
	(r'^productions/(\d+)/add_download_link/$', 'productions.add_download_link', {}, 'production_add_download_link'),
	(r'^productions/(\d+)/edit_download_link/(\d+)/$', 'productions.edit_download_link', {}, 'production_edit_download_link'),
	(r'^productions/(\d+)/delete_download_link/(\d+)/$', 'productions.delete_download_link', {}, 'production_delete_download_link'),
	(r'^productions/(\d+)/edit_external_links/$', 'productions.edit_external_links', {}, 'production_edit_external_links'),
	(r'^productions/(\d+)/add_screenshot/$', 'productions.add_screenshot', {}, 'production_add_screenshot'),
	(r'^productions/(\d+)/screenshots/$', 'productions.screenshots', {}, 'production_screenshots'),
	(r'^productions/(\d+)/delete_screenshot/(\d+)/$', 'productions.delete_screenshot', {}, 'production_delete_screenshot'),
	(r'^productions/(\d+)/edit_soundtracks/$', 'productions.edit_soundtracks', {}, 'production_edit_soundtracks'),
	(r'^productions/(\d+)/add_tag/$', 'productions.add_tag', {}, 'production_add_tag'),
	(r'^productions/(\d+)/remove_tag/(\d+)/$', 'productions.remove_tag', {}, 'production_remove_tag'),
	(r'^productions/(\d+)/delete/$', 'productions.delete', {}, 'delete_production'),

	(r'^groups/$', 'groups.index', {}, 'groups'),
	(r'^groups/(\d+)/$', 'groups.show', {}, 'group'),
	(r'^groups/(\d+)/edit/$', 'groups.edit', {}, 'edit_group'),
	(r'^groups/(\d+)/done/$', 'groups.edit_done', {}, 'edit_group_done'),
	(r'^groups/(\d+)/history/$', 'groups.history', {}, 'group_history'),

	(r'^groups/new/$', 'groups.create', {}, 'new_group'),
	(r'^groups/(\d+)/add_member/$', 'groups.add_member', {}, 'group_add_member'),
	(r'^groups/(\d+)/remove_member/(\d+)/$', 'groups.remove_member', {}, 'group_remove_member'),
	(r'^groups/(\d+)/edit_membership/(\d+)/$', 'groups.edit_membership', {}, 'group_edit_membership'),
	(r'^groups/(\d+)/add_subgroup/$', 'groups.add_subgroup', {}, 'group_add_subgroup'),
	(r'^groups/(\d+)/remove_subgroup/(\d+)/$', 'groups.remove_subgroup', {}, 'group_remove_subgroup'),
	(r'^groups/(\d+)/edit_subgroup/(\d+)/$', 'groups.edit_subgroup', {}, 'group_edit_subgroup'),
	(r'^groups/(\d+)/convert_to_scener/$', 'groups.convert_to_scener', {}, 'group_convert_to_scener'),

	(r'^sceners/$', 'sceners.index', {}, 'sceners'),
	(r'^sceners/(\d+)/$', 'sceners.show', {}, 'scener'),
	(r'^sceners/(\d+)/edit/$', 'sceners.edit', {}, 'edit_scener'),
	(r'^sceners/(\d+)/done/$', 'sceners.edit_done', {}, 'edit_scener_done'),
	(r'^sceners/(\d+)/history/$', 'sceners.history', {}, 'scener_history'),

	(r'^sceners/new/$', 'sceners.create', {}, 'new_scener'),
	(r'^sceners/(\d+)/add_group/$', 'sceners.add_group', {}, 'scener_add_group'),
	(r'^sceners/(\d+)/remove_group/(\d+)/$', 'sceners.remove_group', {}, 'scener_remove_group'),
	(r'^sceners/(\d+)/edit_membership/(\d+)/$', 'sceners.edit_membership', {}, 'scener_edit_membership'),
	(r'^sceners/(\d+)/edit_location/$', 'sceners.edit_location', {}, 'scener_edit_location'),
	(r'^sceners/(\d+)/edit_real_name/$', 'sceners.edit_real_name', {}, 'scener_edit_real_name'),
	(r'^sceners/(\d+)/convert_to_group/$', 'sceners.convert_to_group', {}, 'scener_convert_to_group'),

	(r'^releasers/(\d+)/add_credit/$', 'releasers.add_credit', {}, 'releaser_add_credit'),
	(r'^releasers/(\d+)/edit_credit/(\d+)/(\d+)/$', 'releasers.edit_credit', {}, 'releaser_edit_credit'),
	(r'^releasers/(\d+)/delete_credit/(\d+)/(\d+)/$', 'releasers.delete_credit', {}, 'releaser_delete_credit'),
	(r'^releasers/(\d+)/edit_notes/$', 'releasers.edit_notes', {}, 'releaser_edit_notes'),
	(r'^releasers/(\d+)/edit_nick/(\d+)/$', 'releasers.edit_nick', {}, 'releaser_edit_nick'),
	(r'^releasers/(\d+)/add_nick/$', 'releasers.add_nick', {}, 'releaser_add_nick'),
	(r'^releasers/(\d+)/edit_primary_nick/$', 'releasers.edit_primary_nick', {}, 'releaser_edit_primary_nick'),
	(r'^releasers/(\d+)/change_primary_nick/$', 'releasers.change_primary_nick', {}, 'releaser_change_primary_nick'),
	(r'^releasers/(\d+)/delete_nick/(\d+)/$', 'releasers.delete_nick', {}, 'releaser_delete_nick'),
	(r'^releasers/(\d+)/delete/$', 'releasers.delete', {}, 'delete_releaser'),
	(r'^releasers/(\d+)/edit_external_links/$', 'releasers.edit_external_links', {}, 'releaser_edit_external_links'),

	(r'^parties/$', 'parties.index', {}, 'parties'),
	(r'^parties/by_date/$', 'parties.by_date', {}, 'parties_by_date'),
	(r'^parties/(\d+)/$', 'parties.show', {}, 'party'),
	(r'^parties/(\d+)/history/$', 'parties.history', {}, 'party_history'),
	(r'^parties/series/(\d+)/$', 'parties.show_series', {}, 'party_series'),
	(r'^parties/series/(\d+)/history/$', 'parties.series_history', {}, 'party_series_history'),
	(r'^parties/series/(\d+)/edit/$', 'parties.edit_series', {}, 'party_edit_series'),
	(r'^parties/series/(\d+)/edit_notes/$', 'parties.edit_series_notes', {}, 'party_edit_series_notes'),
	(r'^parties/new/$', 'parties.create', {}, 'new_party'),
	(r'^parties/(\d+)/add_competition/$', 'parties.add_competition', {}, 'party_add_competition'),
	(r'^parties/(\d+)/edit/$', 'parties.edit', {}, 'edit_party'),
	(r'^parties/(\d+)/edit_competition/(\d+)/$', 'parties.edit_competition', {}, 'party_edit_competition'),
	(r'^parties/(\d+)/edit_notes/$', 'parties.edit_notes', {}, 'party_edit_notes'),
	(r'^parties/(\d+)/edit_external_links/$', 'parties.edit_external_links', {}, 'party_edit_external_links'),
	(r'^parties/(\d+)/results_file/(\d+)/$', 'parties.results_file', {}, 'party_results_file'),
	(r'^parties/autocomplete/$', 'parties.autocomplete', {}),
	(r'^parties/(\d+)/edit_invitations/$', 'parties.edit_invitations', {}, 'party_edit_invitations'),

	(r'^competitions/(\d+)/$', 'competitions.show', {}, 'competition'),
	(r'^competitions/(\d+)/history/$', 'competitions.history', {}, 'competition_history'),

	(r'^competition_api/add_placing/(\d+)/$', 'competition_api.add_placing', {}),
	(r'^competition_api/update_placing/(\d+)/$', 'competition_api.update_placing', {}),
	(r'^competition_api/delete_placing/(\d+)/$', 'competition_api.delete_placing', {}),

	(r'^nicks/match/$', 'nicks.match', {}),
	(r'^nicks/byline_match/$', 'nicks.byline_match', {}),

	(r'^platforms/$', 'platforms.index', {}, 'platforms'),
	(r'^platforms/(\d+)/$', 'platforms.show', {}, 'platform'),

)

urlpatterns += patterns('',
	(r'^search/', include('search.urls')),
	(r'^maintenance/', include('maintenance.urls')),
	(r'^pages/', include('pages.urls')),
	(r'^sceneorg/', include('sceneorg.urls')),
)
