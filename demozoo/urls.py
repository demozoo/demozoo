from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, re_path

from demoscene.views import accounts as account_views
from sceneid import auth as sceneid_views


admin.autodiscover()


urlpatterns = [
    re_path(r'^admin/', admin.site.urls),

    re_path(r'^account/$', account_views.index, {}, 'account_index'),
    re_path(r'^account/login/$', account_views.LoginViewWithIPCheck.as_view(), {}, 'log_in'),
    re_path(r'^account/logout/$', auth_views.LogoutView.as_view(next_page='/'), {}, 'log_out'),
    re_path(r'^account/signup/$', account_views.signup, {}, 'user_signup'),
    re_path(r'^account/change_password/$', account_views.change_password, {}, 'account_change_password'),
    # forgotten password
    re_path(r'^account/forgotten_password/$', auth_views.PasswordResetView.as_view(), {}, 'password_reset'),
    re_path(
        r'^account/forgotten_password/success/$', auth_views.PasswordResetDoneView.as_view(), {},
        'password_reset_done'
    ),
    re_path(
        r'^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$',
        auth_views.PasswordResetConfirmView.as_view(), {}, 'password_reset_confirm'
    ),

    re_path(
        r'^account/forgotten_password/done/$', auth_views.PasswordResetCompleteView.as_view(), {},
        'password_reset_complete'
    ),

    re_path(r'^account/sceneid/auth/$', sceneid_views.do_auth_redirect, {}, 'sceneid_auth'),
    re_path(r'^account/sceneid/login/$', sceneid_views.process_response, {}, 'sceneid_return'),
    re_path(r'^account/sceneid/connect/$', sceneid_views.connect_accounts, {}, 'sceneid_connect'),
]

urlpatterns += [
    re_path(r'^', include('demoscene.urls')),
    re_path(r'^', include('homepage.urls')),
    re_path(r'^', include('parties.urls')),
    re_path(r'^', include('comments.urls')),
    re_path(r'^', include('productions.urls')),
    re_path(r'^platforms/', include('platforms.urls')),
    re_path(r'^search/', include('search.urls')),
    re_path(r'^maintenance/', include('maintenance.urls')),
    re_path(r'^pages/', include('pages.urls')),
    re_path(r'^sceneorg/', include('sceneorg.urls')),
    re_path(r'^pouet/', include('pouet.urls')),
    re_path(r'^janeway/', include('janeway.urls')),
    re_path(r'^forums/', include('forums.urls')),
    re_path(r'^api/', include('api.urls')),
    re_path(r'^users/', include('users.urls')),
    re_path(r'^awards/', include('awards.urls')),
    re_path(r'^bbs/', include('bbs.urls')),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
