from django.urls import path

from demoscene.views import groups as groups_views
from demoscene.views import nicks as nicks_views
from demoscene.views import releasers as releasers_views
from demoscene.views import sceners as sceners_views


urlpatterns = [
    path("groups/", groups_views.index, {}, "groups"),
    path("groups/<int:group_id>/", groups_views.show, {}, "group"),
    path("groups/<int:group_id>/history/", groups_views.history, {}, "group_history"),
    path("groups/new/", groups_views.CreateGroupView.as_view(), {}, "new_group"),
    path("groups/<int:group_id>/add_member/", groups_views.AddMemberView.as_view(), {}, "group_add_member"),
    path(
        "groups/<int:group_id>/remove_member/<int:scener_id>/",
        groups_views.RemoveMemberView.as_view(),
        {},
        "group_remove_member",
    ),
    path(
        "groups/<int:group_id>/edit_membership/<int:membership_id>/",
        groups_views.EditMembershipView.as_view(),
        {},
        "group_edit_membership",
    ),
    path("groups/<int:group_id>/add_subgroup/", groups_views.AddSubgroupView.as_view(), {}, "group_add_subgroup"),
    path(
        "groups/<int:group_id>/remove_subgroup/<int:subgroup_id>/",
        groups_views.RemoveSubgroupView.as_view(),
        {},
        "group_remove_subgroup",
    ),
    path(
        "groups/<int:group_id>/edit_subgroup/<int:membership_id>/",
        groups_views.EditSubgroupView.as_view(),
        {},
        "group_edit_subgroup",
    ),
    path(
        "groups/<int:group_id>/convert_to_scener/",
        groups_views.ConvertToScenerView.as_view(),
        {},
        "group_convert_to_scener",
    ),
    path("sceners/", sceners_views.index, {}, "sceners"),
    path("sceners/<int:scener_id>/", sceners_views.show, {}, "scener"),
    path("sceners/<int:scener_id>/history/", sceners_views.history, {}, "scener_history"),
    path("sceners/new/", sceners_views.CreateScenerView.as_view(), {}, "new_scener"),
    path("sceners/<int:scener_id>/add_group/", sceners_views.AddGroupView.as_view(), {}, "scener_add_group"),
    path(
        "sceners/<int:scener_id>/remove_group/<int:group_id>/",
        sceners_views.RemoveGroupView.as_view(),
        {},
        "scener_remove_group",
    ),
    path(
        "sceners/<int:scener_id>/edit_membership/<int:membership_id>/",
        sceners_views.EditMembershipView.as_view(),
        {},
        "scener_edit_membership",
    ),
    path(
        "sceners/<int:scener_id>/edit_location/", sceners_views.EditLocationView.as_view(), {}, "scener_edit_location"
    ),
    path(
        "sceners/<int:scener_id>/edit_real_name/", sceners_views.EditRealNameView.as_view(), {}, "scener_edit_real_name"
    ),
    path(
        "sceners/<int:scener_id>/convert_to_group/",
        sceners_views.ConvertToGroupView.as_view(),
        {},
        "scener_convert_to_group",
    ),
    path("releasers/<int:releaser_id>/edit_notes/", releasers_views.EditNotesView.as_view(), {}, "releaser_edit_notes"),
    path("releasers/<int:releaser_id>/edit_nick/<int:nick_id>/", releasers_views.edit_nick, {}, "releaser_edit_nick"),
    path("releasers/<int:releaser_id>/add_nick/", releasers_views.add_nick, {}, "releaser_add_nick"),
    path(
        "releasers/<int:releaser_id>/edit_primary_nick/",
        releasers_views.edit_primary_nick,
        {},
        "releaser_edit_primary_nick",
    ),
    path(
        "releasers/<int:releaser_id>/change_primary_nick/",
        releasers_views.change_primary_nick,
        {},
        "releaser_change_primary_nick",
    ),
    path(
        "releasers/<int:releaser_id>/delete_nick/<int:nick_id>/",
        releasers_views.DeleteNickView.as_view(),
        {},
        "releaser_delete_nick",
    ),
    path("releasers/<int:releaser_id>/delete/", releasers_views.DeleteReleaserView.as_view(), {}, "delete_releaser"),
    path(
        "releasers/<int:releaser_id>/edit_external_links/",
        releasers_views.edit_external_links,
        {},
        "releaser_edit_external_links",
    ),
    path("releasers/<int:releaser_id>/lock/", releasers_views.LockReleaserView.as_view(), {}, "lock_releaser"),
    path("releasers/<int:releaser_id>/protected/", releasers_views.protected, {}, "releaser_protected"),
    path("nicks/match/", nicks_views.match, {}),
    path("nicks/byline_match/", nicks_views.byline_match, {}),
]
