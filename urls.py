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
)

urlpatterns += patterns('demoscene.views',
	(r'^$', 'home.home', {}, 'home'),
	(r'^productions/$', 'productions.index', {}, 'productions'),
	(r'^productions/(\d+)/$', 'productions.show', {}, 'production'),
	(r'^productions/(\d+)/edit/$', 'productions.edit', {}, 'edit_production'),
)
