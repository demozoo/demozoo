from django.urls import re_path
from django.views.generic import RedirectView

from sceneorg import views as sceneorg_views


urlpatterns = [
    re_path(r"^$", RedirectView.as_view(url="/sceneorg/compofolders/")),
    re_path(r"^compofolders/$", sceneorg_views.compofolders, {}, "sceneorg_compofolders"),
    re_path(r"^compofolders/party/(\d+)/$", sceneorg_views.compofolder_party, {}, "sceneorg_compofolder_party"),
    re_path(r"^compofolders/link/$", sceneorg_views.compofolder_link, {}, "sceneorg_compofolder_link"),
    re_path(r"^compofolders/unlink/$", sceneorg_views.compofolder_unlink, {}, "sceneorg_compofolder_unlink"),
    re_path(r"^compofolders/done/(\d+)/$", sceneorg_views.compofolders_done, {}, "sceneorg_compofolders_done"),
    re_path(
        r"^compofolders/directory/(\d+)/$",
        sceneorg_views.compofolders_show_directory,
        {},
        "sceneorg_compofolders_show_directory",
    ),
    re_path(
        r"^compofolders/competition/(\d+)/$",
        sceneorg_views.compofolders_show_competition,
        {},
        "sceneorg_compofolders_show_competition",
    ),
    re_path(r"^compofiles/$", sceneorg_views.compofiles, {}, "sceneorg_compofiles"),
    re_path(r"^compofiles/dir/(\d+)/$", sceneorg_views.compofile_directory, {}, "sceneorg_compofile_directory"),
    re_path(r"^compofiles/link/$", sceneorg_views.compofile_link, {}, "sceneorg_compofile_link"),
    re_path(r"^compofiles/unlink/$", sceneorg_views.compofile_unlink, {}, "sceneorg_compofile_unlink"),
]
