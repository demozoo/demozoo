from django.urls import path
from django.views.generic import RedirectView

from sceneorg import views as sceneorg_views


urlpatterns = [
    path("", RedirectView.as_view(url="/sceneorg/compofolders/")),
    path("compofolders/", sceneorg_views.compofolders, {}, "sceneorg_compofolders"),
    path("compofolders/party/<int:party_id>/", sceneorg_views.compofolder_party, {}, "sceneorg_compofolder_party"),
    path("compofolders/link/", sceneorg_views.compofolder_link, {}, "sceneorg_compofolder_link"),
    path("compofolders/unlink/", sceneorg_views.compofolder_unlink, {}, "sceneorg_compofolder_unlink"),
    path("compofolders/done/<int:party_id>/", sceneorg_views.compofolders_done, {}, "sceneorg_compofolders_done"),
    path(
        "compofolders/directory/<int:directory_id>/",
        sceneorg_views.compofolders_show_directory,
        {},
        "sceneorg_compofolders_show_directory",
    ),
    path(
        "compofolders/competition/<int:competition_id>/",
        sceneorg_views.compofolders_show_competition,
        {},
        "sceneorg_compofolders_show_competition",
    ),
    path("compofiles/", sceneorg_views.compofiles, {}, "sceneorg_compofiles"),
    path("compofiles/dir/<int:directory_id>/", sceneorg_views.compofile_directory, {}, "sceneorg_compofile_directory"),
    path("compofiles/link/", sceneorg_views.compofile_link, {}, "sceneorg_compofile_link"),
    path("compofiles/unlink/", sceneorg_views.compofile_unlink, {}, "sceneorg_compofile_unlink"),
]
