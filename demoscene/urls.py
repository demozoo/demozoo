from django.urls import re_path

from demoscene.views import groups as groups_views
from demoscene.views import home as home_views
from demoscene.views import nicks as nicks_views
from demoscene.views import releasers as releasers_views
from demoscene.views import sceners as sceners_views


urlpatterns = [
    re_path(r'^error/$', home_views.error_test, {}, 'error_test'),
    re_path(r'^404/$', home_views.page_not_found_test, {}, 'page_not_found_test'),

    re_path(r'^groups/$', groups_views.index, {}, 'groups'),
    re_path(r'^groups/(\d+)/$', groups_views.show, {}, 'group'),
    re_path(r'^groups/(\d+)/history/$', groups_views.history, {}, 'group_history'),

    re_path(r'^groups/new/$', groups_views.create, {}, 'new_group'),
    re_path(r'^groups/(\d+)/add_member/$', groups_views.add_member, {}, 'group_add_member'),
    re_path(r'^groups/(\d+)/remove_member/(\d+)/$', groups_views.remove_member, {}, 'group_remove_member'),
    re_path(r'^groups/(\d+)/edit_membership/(\d+)/$', groups_views.edit_membership, {}, 'group_edit_membership'),
    re_path(r'^groups/(\d+)/add_subgroup/$', groups_views.add_subgroup, {}, 'group_add_subgroup'),
    re_path(
        r'^groups/(\d+)/remove_subgroup/(\d+)/$', groups_views.RemoveSubgroupView.as_view(), {},
        'group_remove_subgroup'
    ),
    re_path(r'^groups/(\d+)/edit_subgroup/(\d+)/$', groups_views.edit_subgroup, {}, 'group_edit_subgroup'),
    re_path(
        r'^groups/(\d+)/convert_to_scener/$', groups_views.ConvertToScenerView.as_view(), {},
        'group_convert_to_scener'
    ),

    re_path(r'^sceners/$', sceners_views.index, {}, 'sceners'),
    re_path(r'^sceners/(\d+)/$', sceners_views.show, {}, 'scener'),
    re_path(r'^sceners/(\d+)/history/$', sceners_views.history, {}, 'scener_history'),

    re_path(r'^sceners/new/$', sceners_views.create, {}, 'new_scener'),
    re_path(r'^sceners/(\d+)/add_group/$', sceners_views.add_group, {}, 'scener_add_group'),
    re_path(r'^sceners/(\d+)/remove_group/(\d+)/$', sceners_views.remove_group, {}, 'scener_remove_group'),
    re_path(r'^sceners/(\d+)/edit_membership/(\d+)/$', sceners_views.edit_membership, {}, 'scener_edit_membership'),
    re_path(r'^sceners/(\d+)/edit_location/$', sceners_views.edit_location, {}, 'scener_edit_location'),
    re_path(r'^sceners/(\d+)/edit_real_name/$', sceners_views.edit_real_name, {}, 'scener_edit_real_name'),
    re_path(
        r'^sceners/(\d+)/convert_to_group/$', sceners_views.ConvertToGroupView.as_view(), {},
        'scener_convert_to_group'
    ),

    re_path(r'^releasers/(\d+)/add_credit/$', releasers_views.add_credit, {}, 'releaser_add_credit'),
    re_path(r'^releasers/(\d+)/edit_credit/(\d+)/(\d+)/$', releasers_views.edit_credit, {}, 'releaser_edit_credit'),
    re_path(
        r'^releasers/(\d+)/delete_credit/(\d+)/(\d+)/$', releasers_views.DeleteCreditView.as_view(), {},
        'releaser_delete_credit'
    ),
    re_path(r'^releasers/(\d+)/edit_notes/$', releasers_views.edit_notes, {}, 'releaser_edit_notes'),
    re_path(r'^releasers/(\d+)/edit_nick/(\d+)/$', releasers_views.edit_nick, {}, 'releaser_edit_nick'),
    re_path(r'^releasers/(\d+)/add_nick/$', releasers_views.add_nick, {}, 'releaser_add_nick'),
    re_path(
        r'^releasers/(\d+)/edit_primary_nick/$', releasers_views.edit_primary_nick, {},
        'releaser_edit_primary_nick'
    ),
    re_path(
        r'^releasers/(\d+)/change_primary_nick/$', releasers_views.change_primary_nick, {},
        'releaser_change_primary_nick'
    ),
    re_path(
        r'^releasers/(\d+)/delete_nick/(\d+)/$', releasers_views.DeleteNickView.as_view(), {},
        'releaser_delete_nick'
    ),
    re_path(r'^releasers/(\d+)/delete/$', releasers_views.DeleteReleaserView.as_view(), {}, 'delete_releaser'),
    re_path(
        r'^releasers/(\d+)/edit_external_links/$', releasers_views.edit_external_links, {},
        'releaser_edit_external_links'
    ),
    re_path(r'^releasers/(\d+)/lock/$', releasers_views.LockReleaserView.as_view(), {}, 'lock_releaser'),
    re_path(r'^releasers/(\d+)/protected/$', releasers_views.protected, {}, 'releaser_protected'),

    re_path(r'^nicks/match/$', nicks_views.match, {}),
    re_path(r'^nicks/byline_match/$', nicks_views.byline_match, {}),
]
