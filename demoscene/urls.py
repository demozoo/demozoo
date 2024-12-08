from django.urls import path

from demoscene.views import groups as groups_views
from demoscene.views import nicks as nicks_views
from demoscene.views import releasers as releasers_views
from demoscene.views import sceners as sceners_views


urlpatterns = [
    path("groups/", groups_views.index, {}, "groups"),
    path("groups/<int:group_id>/", groups_views.show, {}, "group"),
    path("groups/<int:group_id>/history/", groups_views.history, {}, "group_history"),
    path("groups/new/", groups_views.create, {}, "new_group"),
    path("groups/<int:group_id>/add_member/", groups_views.add_member, {}, "group_add_member"),
    path("groups/<int:group_id>/remove_member/<int:scener_id>/", groups_views.remove_member, {}, "group_remove_member"),
    path(
        "groups/<int:group_id>/edit_membership/<int:membership_id>/",
        groups_views.edit_membership,
        {},
        "group_edit_membership",
    ),
    path("groups/<int:group_id>/add_subgroup/", groups_views.add_subgroup, {}, "group_add_subgroup"),
    path(
        "groups/<int:group_id>/remove_subgroup/<int:subgroup_id>/",
        groups_views.RemoveSubgroupView.as_view(),
        {},
        "group_remove_subgroup",
    ),
    path(
        "groups/<int:group_id>/edit_subgroup/<int:membership_id>/",
        groups_views.edit_subgroup,
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
    path("sceners/new/", sceners_views.create, {}, "new_scener"),
    path("sceners/<int:scener_id>/add_group/", sceners_views.add_group, {}, "scener_add_group"),
    path("sceners/<int:scener_id>/remove_group/<int:group_id>/", sceners_views.remove_group, {}, "scener_remove_group"),
    path(
        "sceners/<int:scener_id>/edit_membership/<int:membership_id>/",
        sceners_views.edit_membership,
        {},
        "scener_edit_membership",
    ),
    path("sceners/<int:scener_id>/edit_location/", sceners_views.edit_location, {}, "scener_edit_location"),
    path("sceners/<int:scener_id>/edit_real_name/", sceners_views.edit_real_name, {}, "scener_edit_real_name"),
    path(
        "sceners/<int:scener_id>/convert_to_group/",
        sceners_views.ConvertToGroupView.as_view(),
        {},
        "scener_convert_to_group",
    ),
    path("releasers/<int:releaser_id>/add_credit/", releasers_views.add_credit, {}, "releaser_add_credit"),
    path(
        "releasers/<int:releaser_id>/edit_credit/<int:nick_id>/<int:production_id>/",
        releasers_views.edit_credit,
        {},
        "releaser_edit_credit",
    ),
    path(
        "releasers/<int:releaser_id>/delete_credit/<int:nick_id>/<int:production_id>/",
        releasers_views.DeleteCreditView.as_view(),
        {},
        "releaser_delete_credit",
    ),
    path("releasers/<int:releaser_id>/edit_notes/", releasers_views.edit_notes, {}, "releaser_edit_notes"),
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
