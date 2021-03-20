from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
# Admin backend
from django.contrib import admin


admin.autodiscover()

from django.contrib.auth import views as auth_views

from demoscene.views import accounts as account_views
from demoscene.views import groups as groups_views
from demoscene.views import home as home_views
from demoscene.views import nicks as nicks_views
from demoscene.views import releasers as releasers_views
from demoscene.views import sceners as sceners_views
from sceneid import auth as sceneid_views


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^account/$', account_views.index, {}, 'account_index'),
    url(r'^account/login/$', account_views.LoginViewWithIPCheck.as_view(), {}, 'log_in'),
    url(r'^account/logout/$', auth_views.LogoutView.as_view(next_page='/'), {}, 'log_out'),
    url(r'^account/signup/$', account_views.signup, {}, 'user_signup'),
    url(r'^account/change_password/$', account_views.change_password, {}, 'account_change_password'),
    # forgotten password
    url(r'^account/forgotten_password/$', auth_views.PasswordResetView.as_view(), {}, 'password_reset'),
    url(r'^account/forgotten_password/success/$', auth_views.PasswordResetDoneView.as_view(), {}, 'password_reset_done'),
    url(r'^account/forgotten_password/check/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>\w+-\w+)/$', auth_views.PasswordResetConfirmView.as_view(), {}, 'password_reset_confirm'),

    url(r'^account/forgotten_password/done/$', auth_views.PasswordResetCompleteView.as_view(), {}, 'password_reset_complete'),

    url(r'^account/sceneid/auth/$', sceneid_views.do_auth_redirect, {}, 'sceneid_auth'),
    url(r'^account/sceneid/login/$', sceneid_views.process_response, {}, 'sceneid_return'),
    url(r'^account/sceneid/connect/$', sceneid_views.connect_accounts, {}, 'sceneid_connect'),
]

urlpatterns += [
    url(r'^latest_activity/$', home_views.latest_activity, {}, 'latest_activity'),

    url(r'^error/$', home_views.error_test, {}, 'error_test'),
    url(r'^404/$', home_views.page_not_found_test, {}, 'page_not_found_test'),
    url(r'^edits/$', home_views.recent_edits, {}, 'recent_edits'),

    url(r'^groups/$', groups_views.index, {}, 'groups'),
    url(r'^groups/(\d+)/$', groups_views.show, {}, 'group'),
    url(r'^groups/(\d+)/history/$', groups_views.history, {}, 'group_history'),

    url(r'^groups/new/$', groups_views.create, {}, 'new_group'),
    url(r'^groups/(\d+)/add_member/$', groups_views.add_member, {}, 'group_add_member'),
    url(r'^groups/(\d+)/remove_member/(\d+)/$', groups_views.remove_member, {}, 'group_remove_member'),
    url(r'^groups/(\d+)/edit_membership/(\d+)/$', groups_views.edit_membership, {}, 'group_edit_membership'),
    url(r'^groups/(\d+)/add_subgroup/$', groups_views.add_subgroup, {}, 'group_add_subgroup'),
    url(r'^groups/(\d+)/remove_subgroup/(\d+)/$', groups_views.remove_subgroup, {}, 'group_remove_subgroup'),
    url(r'^groups/(\d+)/edit_subgroup/(\d+)/$', groups_views.edit_subgroup, {}, 'group_edit_subgroup'),
    url(r'^groups/(\d+)/convert_to_scener/$', groups_views.convert_to_scener, {}, 'group_convert_to_scener'),

    url(r'^sceners/$', sceners_views.index, {}, 'sceners'),
    url(r'^sceners/(\d+)/$', sceners_views.show, {}, 'scener'),
    url(r'^sceners/(\d+)/history/$', sceners_views.history, {}, 'scener_history'),

    url(r'^sceners/new/$', sceners_views.create, {}, 'new_scener'),
    url(r'^sceners/(\d+)/add_group/$', sceners_views.add_group, {}, 'scener_add_group'),
    url(r'^sceners/(\d+)/remove_group/(\d+)/$', sceners_views.remove_group, {}, 'scener_remove_group'),
    url(r'^sceners/(\d+)/edit_membership/(\d+)/$', sceners_views.edit_membership, {}, 'scener_edit_membership'),
    url(r'^sceners/(\d+)/edit_location/$', sceners_views.edit_location, {}, 'scener_edit_location'),
    url(r'^sceners/(\d+)/edit_real_name/$', sceners_views.edit_real_name, {}, 'scener_edit_real_name'),
    url(r'^sceners/(\d+)/convert_to_group/$', sceners_views.convert_to_group, {}, 'scener_convert_to_group'),

    url(r'^releasers/(\d+)/add_credit/$', releasers_views.add_credit, {}, 'releaser_add_credit'),
    url(r'^releasers/(\d+)/edit_credit/(\d+)/(\d+)/$', releasers_views.edit_credit, {}, 'releaser_edit_credit'),
    url(r'^releasers/(\d+)/delete_credit/(\d+)/(\d+)/$', releasers_views.delete_credit, {}, 'releaser_delete_credit'),
    url(r'^releasers/(\d+)/edit_notes/$', releasers_views.edit_notes, {}, 'releaser_edit_notes'),
    url(r'^releasers/(\d+)/edit_nick/(\d+)/$', releasers_views.edit_nick, {}, 'releaser_edit_nick'),
    url(r'^releasers/(\d+)/add_nick/$', releasers_views.add_nick, {}, 'releaser_add_nick'),
    url(r'^releasers/(\d+)/edit_primary_nick/$', releasers_views.edit_primary_nick, {}, 'releaser_edit_primary_nick'),
    url(r'^releasers/(\d+)/change_primary_nick/$', releasers_views.change_primary_nick, {}, 'releaser_change_primary_nick'),
    url(r'^releasers/(\d+)/delete_nick/(\d+)/$', releasers_views.delete_nick, {}, 'releaser_delete_nick'),
    url(r'^releasers/(\d+)/delete/$', releasers_views.delete, {}, 'delete_releaser'),
    url(r'^releasers/(\d+)/edit_external_links/$', releasers_views.edit_external_links, {}, 'releaser_edit_external_links'),
    url(r'^releasers/(\d+)/lock/$', releasers_views.lock, {}, 'lock_releaser'),
    url(r'^releasers/(\d+)/protected/$', releasers_views.protected, {}, 'releaser_protected'),

    url(r'^nicks/match/$', nicks_views.match, {}),
    url(r'^nicks/byline_match/$', nicks_views.byline_match, {}),
]

urlpatterns += [
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
