from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from users.views import accounts as account_views
from users.views import sceneid as sceneid_views
from users.views import users as users_views


urlpatterns = [
    path("account/", account_views.index, {}, "account_index"),
    path("account/login/", account_views.LoginViewWithIPCheck.as_view(), {}, "log_in"),
    path("account/logout/", auth_views.LogoutView.as_view(next_page="/"), {}, "log_out"),
    path("account/signup/", account_views.signup, {}, "user_signup"),
    path("account/change_password/", account_views.ChangePasswordView.as_view(), {}, "account_change_password"),
    # forgotten password
    path("account/forgotten_password/", auth_views.PasswordResetView.as_view(), {}, "password_reset"),
    path("account/forgotten_password/success/", auth_views.PasswordResetDoneView.as_view(), {}, "password_reset_done"),
    re_path(
        r"^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$",
        auth_views.PasswordResetConfirmView.as_view(),
        {},
        "password_reset_confirm",
    ),
    path(
        "account/forgotten_password/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        {},
        "password_reset_complete",
    ),
    path("account/sceneid/auth/", sceneid_views.do_auth_redirect, {}, "sceneid_auth"),
    path("account/sceneid/login/", sceneid_views.process_response, {}, "sceneid_return"),
    path("account/sceneid/connect/", sceneid_views.connect_accounts, {}, "sceneid_connect"),
    path("users/", users_views.index, {}, "users_index"),
    path("users/<int:user_id>/", users_views.show, {}, "user"),
]
