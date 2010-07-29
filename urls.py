from django.conf.urls.defaults import *
from django.conf import settings

# Admin backend
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	# Example:
	# (r'^demozoo2/', include('demozoo2.foo.urls')),

	# Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
	# to INSTALLED_APPS to enable admin documentation:
	# (r'^admin/doc/', include('django.contrib.admindocs.urls')),

	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATICROOT}),
	(r'^admin/', include(admin.site.urls)),
	
	(r'^accounts/login/$', 'django.contrib.auth.views.login', {}, 'log_in'),
	(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'log_out'),
	(r'^accounts/signup/$', 'demoscene.views.accounts.signup', {}, 'user_signup'),
)

urlpatterns += patterns('demoscene.views',
	(r'^$', 'home.home', {}, 'home'),
	
	(r'^productions/$', 'productions.index', {}, 'productions'),
	(r'^productions/(\d+)/$', 'productions.show', {}, 'production'),
	(r'^productions/(\d+)/edit/$', 'productions.edit', {}, 'edit_production'),
	(r'^productions/new/$', 'productions.create', {}, 'new_production'),
	(r'^productions/(\d+)/add_credit/$', 'productions.add_credit', {}, 'production_add_credit'),
	(r'^productions/autocomplete/$', 'productions.autocomplete', {}),
	(r'^productions/(\d+)/edit_credit/(\d+)/$', 'productions.edit_credit', {}, 'production_edit_credit'),
	(r'^productions/(\d+)/delete_credit/(\d+)/$', 'productions.delete_credit', {}, 'production_delete_credit'),
	
	(r'^groups/$', 'groups.index', {}, 'groups'),
	(r'^groups/(\d+)/$', 'groups.show', {}, 'group'),
	(r'^groups/(\d+)/edit/$', 'groups.edit', {}, 'edit_group'),
	(r'^groups/new/$', 'groups.create', {}, 'new_group'),
	(r'^groups/(\d+)/add_member/$', 'groups.add_member', {}, 'group_add_member'),
	(r'^groups/(\d+)/remove_member/(\d+)/$', 'groups.remove_member', {}, 'group_remove_member'),
	(r'^groups/autocomplete/$', 'groups.autocomplete', {}),

	(r'^sceners/$', 'sceners.index', {}, 'sceners'),
	(r'^sceners/(\d+)/$', 'sceners.show', {}, 'scener'),
	(r'^sceners/(\d+)/edit/$', 'sceners.edit', {}, 'edit_scener'),
	(r'^sceners/new/$', 'sceners.create', {}, 'new_scener'),
	(r'^sceners/(\d+)/add_group/$', 'sceners.add_group', {}, 'scener_add_group'),
	(r'^sceners/(\d+)/remove_group/(\d+)/$', 'sceners.remove_group', {}, 'scener_remove_group'),
	(r'^sceners/autocomplete/$', 'sceners.autocomplete', {}),
	
	(r'^releasers/autocomplete/$', 'releasers.autocomplete', {}),
	(r'^releasers/(\d+)/add_credit/$', 'releasers.add_credit', {}, 'releaser_add_credit'),
	(r'^releasers/(\d+)/edit_credit/(\d+)/$', 'releasers.edit_credit', {}, 'releaser_edit_credit'),
	(r'^releasers/(\d+)/delete_credit/(\d+)/$', 'releasers.delete_credit', {}, 'releaser_delete_credit'),
	
	(r'^parties/$', 'parties.index', {}, 'parties'),
	(r'^parties/(\d+)/$', 'parties.show', {}, 'party'),
	(r'^parties/series/(\d+)/$', 'parties.show_series', {}, 'party_series'),
	(r'^parties/new/$', 'parties.create', {}, 'new_party'),
	(r'^parties/(\d+)/edit/$', 'parties.edit', {}, 'edit_party'),
	
	(r'^search/', include('search.urls')),
)
