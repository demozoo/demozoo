from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path


admin.autodiscover()

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^', include('demoscene.urls')),
    re_path(r'^', include('homepage.urls')),
    re_path(r'^', include('parties.urls')),
    re_path(r'^', include('comments.urls')),
    re_path(r'^', include('productions.urls')),
    re_path(r'^', include('users.urls')),
    re_path(r'^platforms/', include('platforms.urls')),
    re_path(r'^search/', include('search.urls')),
    re_path(r'^maintenance/', include('maintenance.urls')),
    re_path(r'^pages/', include('pages.urls')),
    re_path(r'^sceneorg/', include('sceneorg.urls')),
    re_path(r'^pouet/', include('pouet.urls')),
    re_path(r'^janeway/', include('janeway.urls')),
    re_path(r'^forums/', include('forums.urls')),
    re_path(r'^api/', include('api.urls')),
    re_path(r'^awards/', include('awards.urls')),
    re_path(r'^bbs/', include('bbs.urls')),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
