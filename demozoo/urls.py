from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from demoscene.views import accounts as account_views
from sceneid import auth as sceneid_views


admin.autodiscover()


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^account/$', account_views.index, {}, 'account_index'),
    url(r'^account/login/$', account_views.LoginViewWithIPCheck.as_view(), {}, 'log_in'),
    url(r'^account/logout/$', auth_views.LogoutView.as_view(next_page='/'), {}, 'log_out'),
    url(r'^account/signup/$', account_views.signup, {}, 'user_signup'),
    url(r'^account/change_password/$', account_views.change_password, {}, 'account_change_password'),
    # forgotten password
    url(r'^account/forgotten_password/$', auth_views.PasswordResetView.as_view(), {}, 'password_reset'),
    url(
        r'^account/forgotten_password/success/$', auth_views.PasswordResetDoneView.as_view(), {},
        'password_reset_done'
    ),
    url(
        r'^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$',
        auth_views.PasswordResetConfirmView.as_view(), {}, 'password_reset_confirm'
    ),

    url(
        r'^account/forgotten_password/done/$', auth_views.PasswordResetCompleteView.as_view(), {},
        'password_reset_complete'
    ),

    url(r'^account/sceneid/auth/$', sceneid_views.do_auth_redirect, {}, 'sceneid_auth'),
    url(r'^account/sceneid/login/$', sceneid_views.process_response, {}, 'sceneid_return'),
    url(r'^account/sceneid/connect/$', sceneid_views.connect_accounts, {}, 'sceneid_connect'),
]

urlpatterns += [
    url(r'^', include('demoscene.urls')),
    url(r'^', include('homepage.urls')),
    url(r'^', include('parties.urls')),
    url(r'^', include('comments.urls')),
    url(r'^', include('productions.urls')),
    url(r'^platforms/', include('platforms.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^maintenance/', include('maintenance.urls')),
    url(r'^pages/', include('pages.urls')),
    url(r'^sceneorg/', include('sceneorg.urls')),
    url(r'^pouet/', include('pouet.urls')),
    url(r'^janeway/', include('janeway.urls')),
    url(r'^forums/', include('forums.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^awards/', include('awards.urls')),
    url(r'^bbs/', include('bbs.urls')),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
