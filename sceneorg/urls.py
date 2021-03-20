from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic import RedirectView

from sceneorg import views as sceneorg_views


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/sceneorg/compofolders/')),
    url(r'^compofolders/$', sceneorg_views.compofolders, {}, 'sceneorg_compofolders'),
    url(r'^compofolders/party/(\d+)/$', sceneorg_views.compofolder_party, {}, 'sceneorg_compofolder_party'),
    url(r'^compofolders/link/$', sceneorg_views.compofolder_link, {}, 'sceneorg_compofolder_link'),
    url(r'^compofolders/unlink/$', sceneorg_views.compofolder_unlink, {}, 'sceneorg_compofolder_unlink'),
    url(r'^compofolders/done/(\d+)/$', sceneorg_views.compofolders_done, {}, 'sceneorg_compofolders_done'),
    url(
        r'^compofolders/directory/(\d+)/$', sceneorg_views.compofolders_show_directory, {},
        'sceneorg_compofolders_show_directory'
    ),
    url(
        r'^compofolders/competition/(\d+)/$', sceneorg_views.compofolders_show_competition, {},
        'sceneorg_compofolders_show_competition'
    ),

    url(r'^compofiles/$', sceneorg_views.compofiles, {}, 'sceneorg_compofiles'),
    url(r'^compofiles/dir/(\d+)/$', sceneorg_views.compofile_directory, {}, 'sceneorg_compofile_directory'),
    url(r'^compofiles/link/$', sceneorg_views.compofile_link, {}, 'sceneorg_compofile_link'),
    url(r'^compofiles/unlink/$', sceneorg_views.compofile_unlink, {}, 'sceneorg_compofile_unlink'),
]
