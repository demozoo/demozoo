import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from common.views import AjaxConfirmationView, writeable_site_required
from demoscene.forms.releaser import (
    GroupNickForm,
    ReleaserEditNotesForm,
    ReleaserExternalLinkFormSet,
    ScenerNickForm,
)
from demoscene.models import Edit, Nick, Releaser
from demoscene.shortcuts import simple_ajax_form


@writeable_site_required
@login_required
def edit_notes(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(releaser.get_absolute_url())

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(
        request,
        "releaser_edit_notes",
        releaser,
        ReleaserEditNotesForm,
        title="Editing notes for %s" % releaser.name,
        update_datestamp=True,
        on_success=success,
    )


@writeable_site_required
@login_required
def edit_nick(request, releaser_id, nick_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)
    primary_nick = releaser.primary_nick

    if not releaser.editable_by_user(request.user):
        raise PermissionDenied

    if releaser.is_group:
        nick_form_class = GroupNickForm
    else:
        nick_form_class = ScenerNickForm
    nick = get_object_or_404(Nick, releaser=releaser, id=nick_id)
    if request.method == "POST":
        form = nick_form_class(releaser, request.POST, instance=nick, for_admin=request.user.is_staff)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get("override_primary_nick") or nick == primary_nick:
                releaser.name = nick.name
            releaser.updated_at = datetime.datetime.now()
            releaser.save()
            form.log_edit(request.user)
            return HttpResponseRedirect(releaser.get_absolute_url() + "?editing=nicks")
    else:
        form = nick_form_class(releaser, instance=nick, for_admin=request.user.is_staff)

    return render(
        request,
        "releasers/edit_nick_form.html",
        {
            "form": form,
            "nick": nick,
            "title": "Editing name: %s" % nick.name,
            "action_url": reverse("releaser_edit_nick", args=[releaser.id, nick.id]),
        },
    )


@writeable_site_required
@login_required
def add_nick(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    if not releaser.editable_by_user(request.user):
        raise PermissionDenied

    if releaser.is_group:
        nick_form_class = GroupNickForm
    else:
        nick_form_class = ScenerNickForm

    if request.method == "POST":
        nick = Nick(releaser=releaser)
        form = nick_form_class(releaser, request.POST, instance=nick, for_admin=request.user.is_staff)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get("override_primary_nick"):
                releaser.name = nick.name
                releaser.save()
            releaser.updated_at = datetime.datetime.now()
            releaser.save()
            form.log_creation(request.user)
            return HttpResponseRedirect(releaser.get_absolute_url() + "?editing=nicks")
    else:
        form = nick_form_class(releaser, for_admin=request.user.is_staff)

    return render(
        request,
        "releasers/add_nick_form.html",
        {
            "form": form,
            "title": "Adding another nick for %s" % releaser.name,
            "action_url": reverse("releaser_add_nick", args=[releaser.id]),
        },
    )


@writeable_site_required
def edit_primary_nick(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)
    if not request.user.is_authenticated:
        # Instead of redirecting back to this edit form after login, redirect to the releaser page.
        # This is because the edit button pointing here is the only one a non-logged-in user sees,
        # so they may intend to edit something else on the releaser page.
        return redirect_to_login(releaser.get_absolute_url())

    if not releaser.editable_by_user(request.user):
        raise PermissionDenied

    return render(
        request,
        "releasers/confirm_edit_nick.html",
        {
            "releaser": releaser,
        },
    )


@writeable_site_required
@login_required
def change_primary_nick(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    if not releaser.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == "POST":
        nick = get_object_or_404(Nick, releaser=releaser, id=request.POST["nick_id"])
        releaser.name = nick.name
        releaser.updated_at = datetime.datetime.now()
        releaser.save()
        Edit.objects.create(
            action_type="change_primary_nick",
            focus=releaser,
            description=("Set primary nick to '%s'" % nick.name),
            user=request.user,
        )
    return HttpResponseRedirect(releaser.get_absolute_url() + "?editing=nicks")


class DeleteNickView(AjaxConfirmationView):
    def get_object(self, request, releaser_id, nick_id):
        self.releaser = Releaser.objects.get(id=releaser_id)
        self.nick = Nick.objects.get(id=nick_id, releaser=self.releaser)

    def is_permitted(self):
        # not allowed to delete primary nick
        return self.releaser.editable_by_user(self.request.user) and not self.nick.is_primary_nick()

    def get_redirect_url(self):
        return self.releaser.get_absolute_url() + "?editing=nicks"

    def get_action_url(self):
        return reverse("releaser_delete_nick", args=[self.releaser.id, self.nick.id])

    def get_message(self):
        if self.nick.is_referenced():
            return """
                Are you sure you want to delete %s's alternative name '%s'?
                This will cause all releases under the name '%s' to be reassigned back to '%s'.
            """ % (self.releaser.name, self.nick.name, self.nick.name, self.releaser.name)
        else:
            return "Are you sure you want to delete %s's alternative name '%s'?" % (self.releaser.name, self.nick.name)

    def get_html_title(self):
        return "Deleting name: %s" % self.nick.name

    def perform_action(self):
        self.nick.reassign_references_and_delete()
        self.releaser.updated_at = datetime.datetime.now()
        self.releaser.save()
        Edit.objects.create(
            action_type="delete_nick",
            focus=self.releaser,
            description=("Deleted nick '%s'" % self.nick.name),
            user=self.request.user,
        )


class DeleteReleaserView(AjaxConfirmationView):
    html_title = "Deleting %s"
    message = "Are you sure you want to delete %s?"
    action_url_path = "delete_releaser"

    def get_object(self, request, releaser_id):
        return Releaser.objects.get(id=releaser_id)

    def is_permitted(self):
        return self.request.user.is_staff

    def get_redirect_url(self):
        if self.object.is_group:
            return reverse("groups")
        else:
            return reverse("sceners")

    def get_cancel_url(self):
        return self.object.get_absolute_url()

    def perform_action(self):
        # insert log entry before actually deleting, so that it doesn't try to
        # insert a null ID for the focus field
        if self.object.is_group:
            Edit.objects.create(
                action_type="delete_group",
                focus=self.object,
                description=("Deleted group '%s'" % self.object.name),
                user=self.request.user,
            )
        else:
            Edit.objects.create(
                action_type="delete_scener",
                focus=self.object,
                description=("Deleted scener '%s'" % self.object.name),
                user=self.request.user,
            )

        self.object.delete()

        messages.success(self.request, "'%s' deleted" % self.object.name)


@writeable_site_required
@login_required
def edit_external_links(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    if not releaser.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == "POST":
        formset = ReleaserExternalLinkFormSet(request.POST, instance=releaser)
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, "releaser_edit_external_links")

            return HttpResponseRedirect(releaser.get_absolute_url())
    else:
        formset = ReleaserExternalLinkFormSet(instance=releaser)
    return render(
        request,
        "releasers/edit_external_links.html",
        {
            "releaser": releaser,
            "formset": formset,
        },
    )


class LockReleaserView(AjaxConfirmationView):
    html_title = "Locking %s"
    message = (
        "Locking down a page is a serious decision and shouldn't be done on a whim - "
        "remember that we want to keep Demozoo as open as possible. "
        "Are you absolutely sure you want to lock '%s'?"
    )
    action_url_path = "lock_releaser"

    def is_permitted(self):  # pragma: no cover
        return self.request.user.is_staff

    def get_object(self, request, releaser_id):
        return Releaser.objects.get(id=releaser_id)

    def perform_action(self):  # pragma: no cover
        Edit.objects.create(
            action_type="lock_releaser",
            focus=self.object,
            description=("Protected releaser '%s'" % self.object.name),
            user=self.request.user,
        )

        self.object.locked = True
        self.object.updated_at = datetime.datetime.now()

        self.object.save()
        messages.success(self.request, "'%s' locked" % self.object.name)


@login_required
def protected(request, releaser_id):
    releaser = get_object_or_404(Releaser, id=releaser_id)

    if request.user.is_staff and request.method == "POST":
        if request.POST.get("yes"):
            Edit.objects.create(
                action_type="unlock_releaser",
                focus=releaser,
                description=("Unprotected releaser '%s'" % releaser.name),
                user=request.user,
            )

            releaser.locked = False
            releaser.updated_at = datetime.datetime.now()

            releaser.save()
            messages.success(request, "'%s' unlocked" % releaser.name)

        return HttpResponseRedirect(releaser.get_absolute_url())

    else:
        return render(
            request,
            "releasers/protected.html",
            {
                "releaser": releaser,
            },
        )
