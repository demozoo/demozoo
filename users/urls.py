from django.contrib.auth import views as auth_views
from django.urls import re_path

from users.views import users as users_views
from users.views import accounts as account_views
from users.views import sceneid as sceneid_views


urlpatterns = [
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

    re_path(r'^users/$', users_views.index, {}, 'users_index'),
    re_path(r'^users/(\d+)/$', users_views.show, {}, 'user'),
]
