from django.conf.urls import *
from django.views.generic import RedirectView

urlpatterns = patterns('sceneorg.views',
	(r'^$', RedirectView.as_view(url='/sceneorg/compofolders/')),
	(r'^compofolders/$', 'compofolders', {}, 'sceneorg_compofolders'),
	(r'^compofolders/party/(\d+)/$', 'compofolder_party', {}, 'sceneorg_compofolder_party'),
	(r'^compofolders/link/$', 'compofolder_link', {}, 'sceneorg_compofolder_link'),
	(r'^compofolders/unlink/$', 'compofolder_unlink', {}, 'sceneorg_compofolder_unlink'),
	(r'^compofolders/done/(\d+)/$', 'compofolders_done', {}, 'sceneorg_compofolders_done'),
	(r'^compofolders/directory/(\d+)/$', 'compofolders_show_directory', {}, 'sceneorg_compofolders_show_directory'),
	(r'^compofolders/competition/(\d+)/$', 'compofolders_show_competition', {}, 'sceneorg_compofolders_show_competition'),
)
