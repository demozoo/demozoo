import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from common.utils.pagination import PaginationControls
from common.views import AjaxConfirmationView, EditingFormView, EditingView, UpdateFormView, writeable_site_required
from demoscene.forms.releaser import (
    CreateScenerForm,
    ScenerEditLocationForm,
    ScenerEditRealNameForm,
    ScenerMembershipForm,
)
from demoscene.models import Edit, Membership, Nick, Releaser
from demoscene.shortcuts import get_page


def index(request):
    nick_page = get_page(
        Nick.objects.filter(releaser__is_group=False)
        .extra(select={"lower_name": "lower(demoscene_nick.name)"})
        .order_by("lower_name"),
        request.GET.get("page", "1"),
    )

    return render(
        request,
        "sceners/index.html",
        {
            "nick_page": nick_page,
            "pagination_controls": PaginationControls(nick_page, reverse("sceners")),
        },
    )


def show(request, scener_id):
    scener = get_object_or_404(Releaser, id=scener_id)
    if scener.is_group:
        return HttpResponseRedirect(scener.get_absolute_url())

    can_edit_real_names = request.user.has_perm("demoscene.change_releaser_real_names")

    external_links = scener.active_external_links.select_related("releaser").defer("releaser__notes")
    if not request.user.is_staff:
        external_links = external_links.exclude(link_class="SlengpungUser")

    external_links = sorted(external_links, key=lambda obj: obj.sort_key)

    parties_organised = (
        scener.parties_organised.select_related("party").defer("party__notes").order_by("-party__start_date_date")
    )
    # order by -role to get Sysop before Co-sysop.
    # Will need to come up with something less hacky if more roles are added :-)
    bbses_operated = (
        scener.bbses_operated.select_related("bbs").defer("bbs__notes").order_by("-is_current", "-role", "bbs__name")
    )

    prompt_to_edit = settings.SITE_IS_WRITEABLE and (request.user.is_staff or not scener.locked)
    can_edit = prompt_to_edit and request.user.is_authenticated

    return render(
        request,
        "sceners/show.html",
        {
            "scener": scener,
            "alternative_nicks": scener.alternative_nicks.prefetch_related("variants"),
            "external_links": external_links,
            "editing_groups": (request.GET.get("editing") == "groups"),
            "editing_nicks": (request.GET.get("editing") == "nicks"),
            "memberships": (
                scener.group_memberships.select_related("group")
                .defer("group__notes")
                .order_by("-is_current", Lower("group__name"))
            ),
            "parties_organised": parties_organised,
            "bbses_operated": bbses_operated,
            "can_edit_real_names": can_edit_real_names,
            "prompt_to_edit": settings.SITE_IS_WRITEABLE and (request.user.is_staff or not scener.locked),
            "can_edit": can_edit,
            "show_locked_button": request.user.is_authenticated and scener.locked,
            "show_lock_button": request.user.is_staff and settings.SITE_IS_WRITEABLE and not scener.locked,
        },
    )


def history(request, scener_id):
    scener = get_object_or_404(Releaser, is_group=False, id=scener_id)
    return render(
        request,
        "sceners/history.html",
        {
            "scener": scener,
            "edits": Edit.for_model(scener, request.user.is_staff),
        },
    )


class EditLocationView(UpdateFormView):
    form_class = ScenerEditLocationForm
    action_url_name = "scener_edit_location"
    update_datestamp = True

    def get_object(self):
        return get_object_or_404(Releaser, is_group=False, id=self.kwargs["scener_id"])

    def can_edit(self, object):
        return object.editable_by_user(self.request.user)

    def get_title(self):
        return "Editing location for %s:" % self.object.name


class EditRealNameView(UpdateFormView):
    form_class = ScenerEditRealNameForm
    action_url_name = "scener_edit_real_name"
    update_datestamp = True
    template_name = "sceners/edit_real_name.html"

    def get_object(self):
        return get_object_or_404(Releaser, is_group=False, id=self.kwargs["scener_id"])

    def can_edit(self, object):
        return self.request.user.has_perm("demoscene.change_releaser_real_names")

    def get_title(self):
        return "Editing %s's real name:" % self.object.name


class CreateScenerView(EditingFormView):
    form_class = CreateScenerForm
    action_url_name = "new_scener"
    title = "New scener"

    def form_valid(self):
        super().form_valid()
        self.form.log_creation(self.request.user)


class AddGroupView(EditingView):
    def prepare(self, request, scener_id):
        self.scener = get_object_or_404(Releaser, is_group=False, id=scener_id)

        if not self.scener.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, scener_id):
        self.form = ScenerMembershipForm(request.POST)
        if self.form.is_valid():
            group = self.form.cleaned_data["group_nick"].commit().releaser
            if not self.scener.group_memberships.filter(group=group).count():
                membership = Membership(
                    member=self.scener,
                    group=self.form.cleaned_data["group_nick"].commit().releaser,
                    is_current=self.form.cleaned_data["is_current"],
                )
                membership.save()
                self.scener.updated_at = datetime.datetime.now()
                self.scener.save()
                description = "Added %s as a member of %s" % (self.scener.name, group.name)
                Edit.objects.create(
                    action_type="add_membership",
                    focus=self.scener,
                    focus2=group,
                    description=description,
                    user=request.user,
                )
            return HttpResponseRedirect(self.scener.get_absolute_url() + "?editing=groups")
        else:
            return self.render_to_response()

    def get(self, request, scener_id):
        self.form = ScenerMembershipForm()
        return self.render_to_response()

    def get_title(self):
        return f"New group for {self.scener.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("scener_add_group", args=[self.scener.id]),
                "submit_button_label": "Add",
            },
        )
        return context


class RemoveGroupView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, scener_id, group_id):
        self.scener = get_object_or_404(Releaser, is_group=False, id=scener_id)
        self.group = get_object_or_404(Releaser, is_group=True, id=group_id)

        if not self.scener.editable_by_user(request.user):
            raise PermissionDenied

        return super().dispatch(request, scener_id, group_id)

    def post(self, request, scener_id, group_id):
        deletion_type = request.POST.get("deletion_type")
        if deletion_type == "ex_member":
            # set membership to is_current=False - do not delete
            self.scener.group_memberships.filter(group=self.group).update(is_current=False)
            self.scener.updated_at = datetime.datetime.now()
            self.scener.save()
            Edit.objects.create(
                action_type="edit_membership",
                focus=self.scener,
                focus2=self.group,
                description="Updated %s's membership of %s: set as ex-member" % (self.scener.name, self.group.name),
                user=request.user,
            )
            return HttpResponseRedirect(self.scener.get_absolute_url() + "?editing=groups")
        elif deletion_type == "full":
            self.scener.group_memberships.filter(group=self.group).delete()
            self.scener.updated_at = datetime.datetime.now()
            self.scener.save()
            description = "Removed %s as a member of %s" % (self.scener.name, self.group.name)
            Edit.objects.create(
                action_type="remove_membership",
                focus=self.scener,
                focus2=self.group,
                description=description,
                user=request.user,
            )
            return HttpResponseRedirect(self.scener.get_absolute_url() + "?editing=groups")
        else:
            self.show_error_message = True
            return self.render_to_response(request)

    def get(self, request, scener_id, group_id):
        self.show_error_message = False
        return self.render_to_response(request)

    def render_to_response(self, request):
        return render(
            request,
            "sceners/remove_group.html",
            {
                "scener": self.scener,
                "group": self.group,
                "show_error_message": self.show_error_message,
            },
        )


class EditMembershipView(EditingView):
    def prepare(self, request, scener_id, membership_id):
        self.scener = get_object_or_404(Releaser, is_group=False, id=scener_id)
        self.membership = get_object_or_404(Membership, member=self.scener, id=membership_id)

        if not self.scener.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, scener_id, membership_id):
        self.form = ScenerMembershipForm(
            request.POST,
            initial={
                "group_nick": self.membership.group.primary_nick,
                "is_current": self.membership.is_current,
            },
        )
        if self.form.is_valid():
            group = self.form.cleaned_data["group_nick"].commit().releaser
            if not self.scener.group_memberships.exclude(id=self.membership.id).filter(group=group).count():
                self.membership.group = group
                self.membership.is_current = self.form.cleaned_data["is_current"]
                self.membership.save()
                self.scener.updated_at = datetime.datetime.now()
                self.scener.save()
                self.form.log_edit(request.user, self.scener, group)
            return HttpResponseRedirect(self.scener.get_absolute_url() + "?editing=groups")
        else:
            return self.render_to_response()

    def get(self, request, scener_id, membership_id):
        self.form = ScenerMembershipForm(
            initial={
                "group_nick": self.membership.group.primary_nick,
                "is_current": self.membership.is_current,
            }
        )
        return self.render_to_response()

    def get_title(self):
        return f"Editing {self.scener.name}'s membership of {self.membership.group.name}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("scener_edit_membership", args=[self.scener.id, self.membership.id]),
                "submit_button_label": "Update membership",
                "delete_url": reverse("scener_remove_group", args=[self.scener.id, self.membership.group.id]),
                "delete_link_text": "Remove from group",
            },
        )
        return context


class ConvertToGroupView(AjaxConfirmationView):
    action_url_path = "scener_convert_to_group"
    html_title = "Converting %s to a group"
    message = "Are you sure you want to convert %s into a group?"

    def get_object(self, request, scener_id):
        return Releaser.objects.get(id=scener_id, is_group=False)

    def is_permitted(self):
        return self.request.user.is_staff and self.object.can_be_converted_to_group()

    def perform_action(self):
        scener = self.object

        scener.is_group = True
        scener.updated_at = datetime.datetime.now()
        scener.save()
        Edit.objects.create(
            action_type="convert_to_group",
            focus=scener,
            description=("Converted %s from a scener to a group" % scener),
            user=self.request.user,
        )
