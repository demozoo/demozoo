from django.conf import settings
from django.conf.urls import include, url

# Admin backend
from django.contrib import admin
admin.autodiscover()

from lib import djapian
djapian.load_indexes()

urlpatterns = [
	url(r'^admin/', include(admin.site.urls)),

	url(r'^account/$', 'demoscene.views.accounts.index', {}, 'account_index'),
	url(r'^account/login/$', 'demoscene.views.accounts.custom_login', {}, 'log_in'),
	url(r'^account/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'log_out'),
	url(r'^account/signup/$', 'demoscene.views.accounts.signup', {}, 'user_signup'),
	url(r'^account/change_password/$', 'demoscene.views.accounts.change_password', {}, 'account_change_password'),
	# forgotten password
	url(r'^account/forgotten_password/$', 'django.contrib.auth.views.password_reset', {'is_admin_site': False}, 'password_reset'),
	url(r'^account/forgotten_password/success/$', 'django.contrib.auth.views.password_reset_done', {}, 'password_reset_done'),
	url(r'^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$', 'django.contrib.auth.views.password_reset_confirm', {}, 'password_reset_confirm'),

	url(r'^account/forgotten_password/done/$', 'django.contrib.auth.views.password_reset_complete', {}, 'password_reset_complete'),

	url(r'^account/sceneid/auth/$', 'sceneid.auth.do_auth_redirect', {}, 'sceneid_auth'),
	url(r'^account/sceneid/login/$', 'sceneid.auth.process_response', {}, 'sceneid_return'),
	url(r'^account/sceneid/connect/$', 'sceneid.auth.connect_accounts', {}, 'sceneid_connect'),
]

urlpatterns += [
	url(r'^latest_activity/$', 'demoscene.views.home.latest_activity', {}, 'latest_activity'),

	url(r'^error/$', 'demoscene.views.home.error_test', {}, 'error_test'),
	url(r'^404/$', 'demoscene.views.home.page_not_found_test', {}, 'page_not_found_test'),
	url(r'^edits/$', 'demoscene.views.home.recent_edits', {}, 'recent_edits'),

	url(r'^groups/$', 'demoscene.views.groups.index', {}, 'groups'),
	url(r'^groups/(\d+)/$', 'demoscene.views.groups.show', {}, 'group'),
	url(r'^groups/(\d+)/history/$', 'demoscene.views.groups.history', {}, 'group_history'),

	url(r'^groups/new/$', 'demoscene.views.groups.create', {}, 'new_group'),
	url(r'^groups/(\d+)/add_member/$', 'demoscene.views.groups.add_member', {}, 'group_add_member'),
	url(r'^groups/(\d+)/remove_member/(\d+)/$', 'demoscene.views.groups.remove_member', {}, 'group_remove_member'),
	url(r'^groups/(\d+)/edit_membership/(\d+)/$', 'demoscene.views.groups.edit_membership', {}, 'group_edit_membership'),
	url(r'^groups/(\d+)/add_subgroup/$', 'demoscene.views.groups.add_subgroup', {}, 'group_add_subgroup'),
	url(r'^groups/(\d+)/remove_subgroup/(\d+)/$', 'demoscene.views.groups.remove_subgroup', {}, 'group_remove_subgroup'),
	url(r'^groups/(\d+)/edit_subgroup/(\d+)/$', 'demoscene.views.groups.edit_subgroup', {}, 'group_edit_subgroup'),
	url(r'^groups/(\d+)/convert_to_scener/$', 'demoscene.views.groups.convert_to_scener', {}, 'group_convert_to_scener'),

	url(r'^sceners/$', 'demoscene.views.sceners.index', {}, 'sceners'),
	url(r'^sceners/(\d+)/$', 'demoscene.views.sceners.show', {}, 'scener'),
	url(r'^sceners/(\d+)/history/$', 'demoscene.views.sceners.history', {}, 'scener_history'),

	url(r'^sceners/new/$', 'demoscene.views.sceners.create', {}, 'new_scener'),
	url(r'^sceners/(\d+)/add_group/$', 'demoscene.views.sceners.add_group', {}, 'scener_add_group'),
	url(r'^sceners/(\d+)/remove_group/(\d+)/$', 'demoscene.views.sceners.remove_group', {}, 'scener_remove_group'),
	url(r'^sceners/(\d+)/edit_membership/(\d+)/$', 'demoscene.views.sceners.edit_membership', {}, 'scener_edit_membership'),
	url(r'^sceners/(\d+)/edit_location/$', 'demoscene.views.sceners.edit_location', {}, 'scener_edit_location'),
	url(r'^sceners/(\d+)/edit_real_name/$', 'demoscene.views.sceners.edit_real_name', {}, 'scener_edit_real_name'),
	url(r'^sceners/(\d+)/convert_to_group/$', 'demoscene.views.sceners.convert_to_group', {}, 'scener_convert_to_group'),

	url(r'^releasers/(\d+)/add_credit/$', 'demoscene.views.releasers.add_credit', {}, 'releaser_add_credit'),
	url(r'^releasers/(\d+)/edit_credit/(\d+)/(\d+)/$', 'demoscene.views.releasers.edit_credit', {}, 'releaser_edit_credit'),
	url(r'^releasers/(\d+)/delete_credit/(\d+)/(\d+)/$', 'demoscene.views.releasers.delete_credit', {}, 'releaser_delete_credit'),
	url(r'^releasers/(\d+)/edit_notes/$', 'demoscene.views.releasers.edit_notes', {}, 'releaser_edit_notes'),
	url(r'^releasers/(\d+)/edit_nick/(\d+)/$', 'demoscene.views.releasers.edit_nick', {}, 'releaser_edit_nick'),
	url(r'^releasers/(\d+)/add_nick/$', 'demoscene.views.releasers.add_nick', {}, 'releaser_add_nick'),
	url(r'^releasers/(\d+)/edit_primary_nick/$', 'demoscene.views.releasers.edit_primary_nick', {}, 'releaser_edit_primary_nick'),
	url(r'^releasers/(\d+)/change_primary_nick/$', 'demoscene.views.releasers.change_primary_nick', {}, 'releaser_change_primary_nick'),
	url(r'^releasers/(\d+)/delete_nick/(\d+)/$', 'demoscene.views.releasers.delete_nick', {}, 'releaser_delete_nick'),
	url(r'^releasers/(\d+)/delete/$', 'demoscene.views.releasers.delete', {}, 'delete_releaser'),
	url(r'^releasers/(\d+)/edit_external_links/$', 'demoscene.views.releasers.edit_external_links', {}, 'releaser_edit_external_links'),

	url(r'^nicks/match/$', 'demoscene.views.nicks.match', {}),
	url(r'^nicks/byline_match/$', 'demoscene.views.nicks.byline_match', {}),
]

urlpatterns += [
	url(r'^', include('homepage.urls')),
	url(r'^', include('parties.urls')),
	url(r'^', include('comments.urls')),
	url(r'^', include('productions.urls')),
	url(r'^platforms/', include('platforms.urls')),
	url(r'^search/', include('search.urls')),
	url(r'^maintenance/', include('maintenance.urls')),
	url(r'^pages/', include('pages.urls')),
	url(r'^sceneorg/', include('sceneorg.urls')),
	url(r'^forums/', include('forums.urls')),
	url(r'^api/', include('api.urls')),
	url(r'^users/', include('users.urls')),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:
	import debug_toolbar
	urlpatterns = [
		url(r'^__debug__/', include(debug_toolbar.urls)),
	] + urlpatterns
