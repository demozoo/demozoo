from django.conf.urls import patterns, include

# Admin backend
from django.contrib import admin
admin.autodiscover()

from lib import djapian
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
	(r'^account/change_password/$', 'demoscene.views.accounts.change_password', {}, 'account_change_password'),
	# forgotten password
	(r'^account/forgotten_password/$', 'django.contrib.auth.views.password_reset', {'is_admin_site': False}, 'password_reset'),
	(r'^account/forgotten_password/success/$', 'django.contrib.auth.views.password_reset_done', {}, 'password_reset_done'),
	(r'^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$', 'django.contrib.auth.views.password_reset_confirm', {}, 'password_reset_confirm'),

	# temporary route for password reset emails sent prior to django 1.6
	# (r'^account/forgotten_password/confirm/(?P<uidb36>\w+)/(?P<token>\w+-\w+)/$', 'django.contrib.auth.views.password_reset_confirm', {}),

	(r'^account/forgotten_password/done/$', 'django.contrib.auth.views.password_reset_complete', {}, 'password_reset_complete'),

	(r'^account/sceneid/auth/$', 'sceneid.auth.do_auth_redirect', {}, 'sceneid_auth'),
	(r'^account/sceneid/login/$', 'sceneid.auth.process_response', {}, 'sceneid_return'),
	(r'^account/sceneid/connect/$', 'sceneid.auth.connect_accounts', {}, 'sceneid_connect'),
)

urlpatterns += patterns('demoscene.views',
	(r'^latest_activity/$', 'home.latest_activity', {}, 'latest_activity'),

	(r'^error/$', 'home.error_test', {}, 'error_test'),
	(r'^404/$', 'home.page_not_found_test', {}, 'page_not_found_test'),
	(r'^edits/$', 'home.recent_edits', {}, 'recent_edits'),

	(r'^groups/$', 'groups.index', {}, 'groups'),
	(r'^groups/(\d+)/$', 'groups.show', {}, 'group'),
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

	(r'^nicks/match/$', 'nicks.match', {}),
	(r'^nicks/byline_match/$', 'nicks.byline_match', {}),
)

urlpatterns += patterns('',
	(r'^', include('homepage.urls')),
	(r'^', include('parties.urls')),
	(r'^', include('comments.urls')),
	(r'^', include('productions.urls')),
	(r'^platforms/', include('platforms.urls')),
	(r'^search/', include('search.urls')),
	(r'^maintenance/', include('maintenance.urls')),
	(r'^pages/', include('pages.urls')),
	(r'^sceneorg/', include('sceneorg.urls')),
	(r'^forums/', include('forums.urls')),
	(r'^api/', include('api.urls')),
	(r'^users/', include('users.urls')),
)
