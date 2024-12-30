import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from common.utils.pagination import PaginationControls
from common.views import AjaxConfirmationView, EditingFormView, EditingView
from demoscene.forms.releaser import CreateGroupForm, GroupMembershipForm, GroupSubgroupForm
from demoscene.models import Edit, Membership, Nick, Releaser
from demoscene.shortcuts import get_page


def index(request):
    nick_page = get_page(
        Nick.objects.filter(releaser__is_group=True)
        .extra(select={"lower_name": "lower(demoscene_nick.name)"})
        .order_by("lower_name"),
        request.GET.get("page", "1"),
    )

    return render(
        request,
        "groups/index.html",
        {
            "nick_page": nick_page,
            "pagination_controls": PaginationControls(nick_page, reverse("groups")),
        },
    )


def show(request, group_id):
    group = get_object_or_404(Releaser, id=group_id)
    if not group.is_group:
        return HttpResponseRedirect(group.get_absolute_url())

    external_links = group.active_external_links.select_related("releaser").defer("releaser__notes")
    external_links = sorted(external_links, key=lambda obj: obj.sort_key)
    parties_organised = (
        group.parties_organised.select_related("party").defer("party__notes").order_by("-party__start_date_date")
    )
    bbs_affiliations = (
        group.bbs_affiliations.select_related("bbs")
        .defer("bbs__notes")
        .order_by(
            Concat("role", Value("999")),  # sort role='' after the numbered ones. Ewww.
            "bbs__name",
        )
    )

    prompt_to_edit = settings.SITE_IS_WRITEABLE and (request.user.is_staff or not group.locked)
    can_edit = prompt_to_edit and request.user.is_authenticated

    return render(
        request,
        "groups/show.html",
        {
            "group": group,
            "alternative_nicks": group.alternative_nicks.prefetch_related("variants"),
            "editing_nicks": (request.GET.get("editing") == "nicks"),
            "supergroupships": (
                group.group_memberships.all()
                .select_related("group")
                .defer("group__notes")
                .order_by("-is_current", Lower("group__name"))
            ),
            "memberships": (
                group.member_memberships.filter(member__is_group=False)
                .select_related("member")
                .defer("member__notes")
                .order_by("-is_current", Lower("member__name"))
            ),
            "editing_members": (request.GET.get("editing") == "members"),
            "editing_subgroups": (request.GET.get("editing") == "subgroups"),
            "subgroupships": (
                group.member_memberships.filter(member__is_group=True)
                .select_related("member")
                .defer("member__notes")
                .order_by("-is_current", Lower("member__name"))
            ),
            "parties_organised": parties_organised,
            "bbs_affiliations": bbs_affiliations,
            "member_productions": (
                group.member_productions()
                .prefetch_related("author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types")
                .defer("notes", "author_nicks__releaser__notes", "author_affiliation_nicks__releaser__notes")
                .order_by("-release_date_date", "release_date_precision", "-sortable_title")
            ),
            "external_links": external_links,
            "prompt_to_edit": prompt_to_edit,
            "can_edit": can_edit,
            "show_locked_button": request.user.is_authenticated and group.locked,
            "show_lock_button": request.user.is_staff and settings.SITE_IS_WRITEABLE and not group.locked,
        },
    )


def history(request, group_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)
    return render(
        request,
        "groups/history.html",
        {
            "group": group,
            "edits": Edit.for_model(group, request.user.is_staff),
        },
    )


class CreateGroupView(EditingFormView):
    form_class = CreateGroupForm
    action_url_name = "new_group"
    title = "New group"

    def form_valid(self):
        super().form_valid()
        self.form.log_creation(self.request.user)


class AddMemberView(EditingView):
    def prepare(self, request, group_id):
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)

        if not self.group.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, group_id):
        self.form = GroupMembershipForm(request.POST)
        if self.form.is_valid():
            member = self.form.cleaned_data["scener_nick"].commit().releaser
            if not self.group.member_memberships.filter(member=member).count():
                membership = Membership(
                    member=member, group=self.group, is_current=self.form.cleaned_data["is_current"]
                )
                membership.save()
                self.group.updated_at = datetime.datetime.now()
                self.group.save()
                description = "Added %s as a member of %s" % (member.name, self.group.name)
                Edit.objects.create(
                    action_type="add_membership",
                    focus=member,
                    focus2=self.group,
                    description=description,
                    user=request.user,
                )
            return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=members")
        else:
            return self.render_to_response()

    def get(self, request, group_id):
        self.form = GroupMembershipForm()
        return self.render_to_response()

    def get_title(self):
        return f"New member for {self.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("group_add_member", args=[self.group.id]),
                "submit_button_label": "Add member",
            },
        )
        return context


class RemoveMemberView(EditingView):
    template_name = "groups/remove_member.html"

    def prepare(self, request, group_id, scener_id):
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)
        self.scener = get_object_or_404(Releaser, is_group=False, id=scener_id)

        if not self.group.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, group_id, scener_id):
        deletion_type = request.POST.get("deletion_type")
        if deletion_type == "ex_member":
            # set membership to is_current=False - do not delete
            self.group.member_memberships.filter(member=self.scener).update(is_current=False)
            self.group.updated_at = datetime.datetime.now()
            self.group.save()
            Edit.objects.create(
                action_type="edit_membership",
                focus=self.scener,
                focus2=self.group,
                description="Updated %s's membership of %s: set as ex-member" % (self.scener.name, self.group.name),
                user=request.user,
            )
            return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=members")
        elif deletion_type == "full":
            self.group.member_memberships.filter(member=self.scener).delete()
            self.group.updated_at = datetime.datetime.now()
            self.group.save()
            description = "Removed %s as a member of %s" % (self.scener.name, self.group.name)
            Edit.objects.create(
                action_type="remove_membership",
                focus=self.scener,
                focus2=self.group,
                description=description,
                user=request.user,
            )
            return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=members")
        else:
            self.show_error_message = True
            return self.render_to_response()

    def get(self, request, group_id, scener_id):
        self.show_error_message = False
        return self.render_to_response()

    def get_title(self):
        return f"Removing {self.scener.name} as a member of {self.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "group": self.group,
                "scener": self.scener,
                "show_error_message": self.show_error_message,
                "action_url": reverse("group_remove_member", args=[self.group.id, self.scener.id]),
                "html_form_class": "remove_member_form",
                "submit_button_label": "Remove membership",
            },
        )
        return context


class EditMembershipView(EditingView):
    def prepare(self, request, group_id, membership_id):
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)
        self.membership = get_object_or_404(Membership, group=self.group, id=membership_id)

        if not self.group.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, group_id, membership_id):
        if request.method == "POST":
            self.form = GroupMembershipForm(
                request.POST,
                initial={
                    "scener_nick": self.membership.member.primary_nick,
                    "is_current": self.membership.is_current,
                },
            )
            if self.form.is_valid():
                member = self.form.cleaned_data["scener_nick"].commit().releaser
                # skip saving if the value of the member (scener) field duplicates an existing one on this group
                if not self.group.member_memberships.exclude(id=self.membership.id).filter(member=member).count():
                    self.membership.member = member
                    self.membership.is_current = self.form.cleaned_data["is_current"]
                    self.membership.save()
                    self.group.updated_at = datetime.datetime.now()
                    self.group.save()
                    self.form.log_edit(request.user, member, self.group)

                return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=members")
            else:
                return self.render_to_response()

    def get(self, request, group_id, membership_id):
        self.form = GroupMembershipForm(
            initial={
                "scener_nick": self.membership.member.primary_nick,
                "is_current": self.membership.is_current,
            }
        )
        return self.render_to_response()

    def get_title(self):
        return f"Editing {self.membership.member.name}'s membership of {self.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("group_edit_membership", args=[self.group.id, self.membership.id]),
                "submit_button_label": "Update membership",
                "delete_url": reverse("group_remove_member", args=[self.group.id, self.membership.member.id]),
                "delete_link_text": "Remove from group",
            },
        )
        return context


class AddSubgroupView(EditingView):
    def prepare(self, request, group_id):
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)

        if not self.group.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, group_id):
        self.form = GroupSubgroupForm(request.POST)
        if self.form.is_valid():
            member = self.form.cleaned_data["subgroup_nick"].commit().releaser
            if not self.group.member_memberships.filter(member=member).count():
                membership = Membership(
                    member=member, group=self.group, is_current=self.form.cleaned_data["is_current"]
                )
                membership.save()
                self.group.updated_at = datetime.datetime.now()
                self.group.save()
                description = "Added %s as a subgroup of %s" % (member.name, self.group.name)
                Edit.objects.create(
                    action_type="add_subgroup",
                    focus=member,
                    focus2=self.group,
                    description=description,
                    user=request.user,
                )
            return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=subgroups")
        else:
            return self.render_to_response()

    def get(self, request, group_id):
        self.form = GroupSubgroupForm()
        return self.render_to_response()

    def get_title(self):
        return f"New subgroup for {self.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("group_add_subgroup", args=[self.group.id]),
                "submit_button_label": "Add subgroup",
            },
        )
        return context


class RemoveSubgroupView(AjaxConfirmationView):
    def get_object(self, request, group_id, subgroup_id):
        self.group = Releaser.objects.get(id=group_id, is_group=True)
        self.subgroup = Releaser.objects.get(id=subgroup_id, is_group=True)

    def is_permitted(self):
        return self.group.editable_by_user(self.request.user)

    def get_redirect_url(self):
        return self.group.get_absolute_url() + "?editing=subgroups"

    def get_action_url(self):
        return reverse("group_remove_subgroup", args=[self.group.id, self.subgroup.id])

    def get_message(self):
        return "Are you sure you want to remove %s as a subgroup of %s?" % (self.subgroup.name, self.group.name)

    def get_html_title(self):
        return "Removing %s from %s" % (self.subgroup.name, self.group.name)

    def perform_action(self):
        self.group.member_memberships.filter(member=self.subgroup).delete()
        self.group.updated_at = datetime.datetime.now()
        self.group.save()
        description = "Removed %s as a subgroup of %s" % (self.subgroup.name, self.group.name)
        Edit.objects.create(
            action_type="remove_membership",
            focus=self.subgroup,
            focus2=self.group,
            description=description,
            user=self.request.user,
        )


class EditSubgroupView(EditingView):
    def prepare(self, request, group_id, membership_id):
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)
        self.membership = get_object_or_404(Membership, group=self.group, id=membership_id)

        if not self.group.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, group_id, membership_id):
        self.form = GroupSubgroupForm(
            request.POST,
            initial={
                "subgroup_nick": self.membership.member.primary_nick,
                "is_current": self.membership.is_current,
            },
        )
        if self.form.is_valid():
            member = self.form.cleaned_data["subgroup_nick"].commit().releaser
            if not self.group.member_memberships.exclude(id=self.membership.id).filter(member=member).count():
                self.membership.member = member
                self.membership.is_current = self.form.cleaned_data["is_current"]
                self.membership.save()
                self.group.updated_at = datetime.datetime.now()
                self.group.save()
                self.form.log_edit(request.user, member, self.group)
            return HttpResponseRedirect(self.group.get_absolute_url() + "?editing=subgroups")
        else:
            return self.render_to_response()

    def get(self, request, group_id, membership_id):
        self.form = GroupSubgroupForm(
            initial={
                "subgroup_nick": self.membership.member.primary_nick,
                "is_current": self.membership.is_current,
            }
        )
        return self.render_to_response()

    def get_title(self):
        return f"Editing {self.membership.member.name} as a subgroup of {self.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("group_edit_subgroup", args=[self.group.id, self.membership.id]),
                "submit_button_label": "Update subgroup",
                "delete_url": reverse("group_remove_subgroup", args=[self.group.id, self.membership.member.id]),
                "delete_link_text": "Remove from group",
            },
        )
        return context


class ConvertToScenerView(AjaxConfirmationView):
    action_url_path = "group_convert_to_scener"
    html_title = "Converting %s to a scener"
    message = "Are you sure you want to convert %s into a scener?"

    def get_object(self, request, group_id):
        return Releaser.objects.get(id=group_id, is_group=True)

    def is_permitted(self):
        return self.request.user.is_staff and self.object.can_be_converted_to_scener()

    def perform_action(self):
        group = self.object

        group.is_group = False
        group.updated_at = datetime.datetime.now()
        group.save()
        for nick in group.nicks.all():
            # sceners do not have specific 'abbreviation' fields on their nicks
            if nick.abbreviation:
                nick.abbreviation = ""
                nick.save()

        Edit.objects.create(
            action_type="convert_to_scener",
            focus=group,
            description=("Converted %s from a group to a scener" % group),
            user=self.request.user,
        )
