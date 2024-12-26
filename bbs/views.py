import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from taggit.models import Tag

from bbs.forms import (
    AffiliationForm,
    AlternativeNameFormSet,
    BBSEditNotesForm,
    BBSExternalLinkFormSet,
    BBSForm,
    BBSTagsForm,
    BBSTextAdFormset,
    BBStroFormset,
    OperatorForm,
)
from bbs.models import BBS, Affiliation, Operator, TextAd
from comments.forms import CommentForm
from comments.models import Comment
from common.utils.pagination import PaginationControls, extract_query_params
from common.views import (
    AddTagView,
    AjaxConfirmationView,
    EditTagsView,
    EditTextFilesView,
    RemoveTagView,
    UpdateFormView,
    writeable_site_required,
)
from demoscene.models import Edit
from demoscene.shortcuts import get_page
from search.indexing import index as search_index


def index(request):
    order = request.GET.get("order", "name")
    asc = request.GET.get("dir", "asc") == "asc"

    queryset = BBS.objects.all()

    if order == "added":
        queryset = queryset.order_by("%screated_at" % ("" if asc else "-"))
    else:  # name
        queryset = queryset.order_by(Lower("name")) if asc else queryset.order_by(Lower("name").desc())

    page = get_page(queryset, request.GET.get("page", "1"))

    return render(
        request,
        "bbs/index.html",
        {
            "page": page,
            "pagination_controls": PaginationControls(
                page, reverse("bbses"), extract_query_params(request.GET, ["order", "dir"])
            ),
            "order": order,
            "asc": asc,
        },
    )


def tagged(request, tag_name):
    try:
        tag = Tag.objects.get(name=tag_name)
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
    queryset = BBS.objects.filter(tags__name=tag_name).order_by("name")

    page = get_page(queryset, request.GET.get("page", "1"))

    return render(
        request,
        "bbs/tagged.html",
        {
            "tag": tag,
            "page": page,
            "pagination_controls": PaginationControls(page, reverse("bbses_tagged", args=[tag_name])),
        },
    )


def show(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    bbstros = bbs.bbstros.order_by("-release_date_date", "title").prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types"
    )

    # order by -role to get Sysop before Co-sysop.
    # Will need to come up with something less hacky if more roles are added :-)
    staff = (
        bbs.staff.select_related("releaser").defer("releaser__notes").order_by("-is_current", "-role", "releaser__name")
    )

    affiliations = (
        bbs.affiliations.select_related("group")
        .defer("group__notes")
        .order_by(
            Concat("role", Value("999")),  # sort role='' after the numbered ones. Ewww.
            "group__name",
        )
    )

    external_links = bbs.active_external_links.select_related("bbs").defer("bbs__notes")

    if request.user.is_authenticated:
        tags_form = BBSTagsForm(instance=bbs)
        comment = Comment(commentable=bbs, user=request.user)
        comment_form = CommentForm(instance=comment, prefix="comment")
    else:
        tags_form = None
        comment_form = None

    return render(
        request,
        "bbs/show.html",
        {
            "bbs": bbs,
            "prompt_to_edit": settings.SITE_IS_WRITEABLE,
            "can_edit": settings.SITE_IS_WRITEABLE and request.user.is_authenticated,
            "alternative_names": bbs.alternative_names.all(),
            "bbstros": bbstros,
            "staff": staff,
            "editing_staff": (request.GET.get("editing") == "staff"),
            "affiliations": affiliations,
            "editing_affiliations": (request.GET.get("editing") == "affiliations"),
            "text_ads": bbs.text_ads.all(),
            "tags": bbs.tags.order_by("name"),
            "tags_form": tags_form,
            "external_links": external_links,
            "comment_form": comment_form,
        },
    )


@writeable_site_required
@login_required
def create(request):
    if request.method == "POST":
        bbs = BBS()
        form = BBSForm(request.POST, instance=bbs)
        alternative_name_formset = AlternativeNameFormSet(request.POST, instance=bbs)
        form_is_valid = form.is_valid()
        alternative_name_formset_is_valid = alternative_name_formset.is_valid()
        if form_is_valid and alternative_name_formset_is_valid:
            form.save()
            alternative_name_formset.save()
            form.log_creation(request.user)
            search_index(bbs)

            messages.success(request, "BBS added")
            return redirect("bbs", bbs.id)
    else:
        form = BBSForm()
        alternative_name_formset = AlternativeNameFormSet()
    return render(
        request,
        "bbs/bbs_form.html",
        {
            "form": form,
            "alternative_name_formset": alternative_name_formset,
            "title": "New BBS",
            "html_title": "New bbs",
            "action_url": reverse("new_bbs"),
        },
    )


@writeable_site_required
def edit(request, bbs_id):
    if not request.user.is_authenticated:
        # Instead of redirecting back to this edit form after login, redirect to the BBS page.
        # This is because the edit button pointing here is the only one a non-logged-in user sees,
        # so they may intend to edit something else on the BBS page.
        return redirect_to_login(reverse("bbs", args=[bbs_id]))

    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == "POST":
        form = BBSForm(request.POST, instance=bbs)
        alternative_name_formset = AlternativeNameFormSet(
            request.POST, instance=bbs, queryset=bbs.alternative_names.all()
        )
        form_is_valid = form.is_valid()
        alternative_name_formset_is_valid = alternative_name_formset.is_valid()
        if form_is_valid and alternative_name_formset_is_valid:
            form.save()
            alternative_name_formset.save()
            search_index(bbs)

            edit_description = form.changed_data_description
            if alternative_name_formset.has_changed():
                alternative_names = ", ".join([name.name for name in bbs.alternative_names.all()])
                if edit_description:
                    edit_description += ", alternative names to %s" % alternative_names
                else:
                    edit_description = "Set alternative names to %s" % alternative_names

            if edit_description:
                Edit.objects.create(action_type="edit_bbs", focus=bbs, description=edit_description, user=request.user)

            messages.success(request, "BBS updated")
            return redirect("bbs", bbs.id)
    else:
        form = BBSForm(instance=bbs)
        alternative_name_formset = AlternativeNameFormSet(instance=bbs, queryset=bbs.alternative_names.all())

    title = "Editing BBS: %s" % bbs.name
    return render(
        request,
        "bbs/bbs_form.html",
        {
            "html_title": title,
            "title": title,
            "form": form,
            "alternative_name_formset": alternative_name_formset,
            "action_url": reverse("edit_bbs", args=[bbs.id]),
        },
    )


class EditNotesView(UpdateFormView):
    form_class = BBSEditNotesForm
    action_url_name = "bbs_edit_notes"

    def get_object(self):
        return get_object_or_404(BBS, id=self.kwargs["bbs_id"])

    def can_edit(self, object):
        return self.request.user.is_staff

    def get_title(self):
        return "Editing notes for %s" % self.object.name


class DeleteBBSView(AjaxConfirmationView):
    html_title = "Deleting %s"
    message = "Are you sure you want to delete %s?"
    action_url_path = "delete_bbs"

    def get_object(self, request, bbs_id):
        return BBS.objects.get(id=bbs_id)

    def is_permitted(self):
        return self.request.user.is_staff

    def get_redirect_url(self):
        return reverse("bbses")

    def get_cancel_url(self):
        return self.object.get_absolute_url()

    def perform_action(self):
        # insert log entry before actually deleting, so that it doesn't try to
        # insert a null ID for the focus field
        Edit.objects.create(
            action_type="delete_bbs",
            focus=self.object,
            description=("Deleted BBS '%s'" % self.object.name),
            user=self.request.user,
        )
        self.object.delete()
        messages.success(self.request, "'%s' deleted" % self.object.name)


@writeable_site_required
@login_required
def edit_bbstros(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    initial_forms = [{"production": production} for production in bbs.bbstros.all()]

    if request.method == "POST":
        formset = BBStroFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            bbstros = [
                prod_form.cleaned_data["production"].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms and "production" in prod_form.cleaned_data
            ]
            bbs.bbstros.set(bbstros)

            if formset.has_changed():
                bbstro_titles = [prod.title for prod in bbstros] or ["none"]
                bbstro_titles = ", ".join(bbstro_titles)
                Edit.objects.create(
                    action_type="edit_bbs_bbstros",
                    focus=bbs,
                    description="Set promoted in to %s" % bbstro_titles,
                    user=request.user,
                )
                bbs.updated_at = datetime.datetime.now()
                bbs.save(update_fields=["updated_at"])

            return redirect("bbs", bbs.id)
    else:
        formset = BBStroFormset(initial=initial_forms)

    title = f"Editing productions promoting {bbs.name}"

    return render(
        request,
        "bbs/edit_bbstros.html",
        {
            "bbs": bbs,
            "formset": formset,
            "title": title,
            "html_title": title,
            "action_url": reverse("bbs_edit_bbstros", args=[bbs.id]),
            "submit_button_label": "Update production list",
        },
    )


def history(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    return render(
        request,
        "bbs/history.html",
        {
            "bbs": bbs,
            "edits": Edit.for_model(bbs, request.user.is_staff),
        },
    )


@writeable_site_required
@login_required
def add_operator(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == "POST":
        form = OperatorForm(request.POST)
        if form.is_valid():
            releaser = form.cleaned_data["releaser_nick"].commit().releaser
            operator = Operator(
                releaser=releaser, bbs=bbs, role=form.cleaned_data["role"], is_current=form.cleaned_data["is_current"]
            )
            operator.save()
            description = "Added %s as staff member of %s" % (releaser.name, bbs.name)
            Edit.objects.create(
                action_type="add_bbs_operator", focus=releaser, focus2=bbs, description=description, user=request.user
            )
            bbs.updated_at = datetime.datetime.now()
            bbs.save(update_fields=["updated_at"])
            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=staff")
    else:
        form = OperatorForm()

    title = f"Add staff member for {bbs.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("bbs_add_operator", args=[bbs.id]),
            "submit_button_label": "Add staff member",
        },
    )


@writeable_site_required
@login_required
def edit_operator(request, bbs_id, operator_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    operator = get_object_or_404(Operator, bbs=bbs, id=operator_id)

    if request.method == "POST":
        form = OperatorForm(
            request.POST,
            initial={
                "releaser_nick": operator.releaser.primary_nick,
                "role": operator.role,
                "is_current": operator.is_current,
            },
        )
        if form.is_valid():
            releaser = form.cleaned_data["releaser_nick"].commit().releaser
            operator.releaser = releaser
            operator.role = form.cleaned_data["role"]
            operator.is_current = form.cleaned_data["is_current"]
            operator.save()
            form.log_edit(request.user, releaser, bbs)
            bbs.updated_at = datetime.datetime.now()
            bbs.save(update_fields=["updated_at"])

            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=staff")
    else:
        form = OperatorForm(
            initial={
                "releaser_nick": operator.releaser.primary_nick,
                "role": operator.role,
                "is_current": operator.is_current,
            }
        )

    title = f"Editing {operator.releaser.name} as staff member of {bbs.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("bbs_edit_operator", args=[bbs.id, operator.id]),
            "submit_button_label": "Update staff member",
            "delete_url": reverse("bbs_remove_operator", args=[bbs.id, operator.id]),
            "delete_link_text": "Remove staff member",
        },
    )


class RemoveOperatorView(AjaxConfirmationView):
    def get_object(self, request, bbs_id, operator_id):
        self.bbs = BBS.objects.get(id=bbs_id)
        self.operator = Operator.objects.get(bbs=self.bbs, id=operator_id)

    def get_redirect_url(self):
        return self.bbs.get_absolute_url() + "?editing=staff"

    def get_action_url(self):
        return reverse("bbs_remove_operator", args=[self.bbs.id, self.operator.id])

    def get_message(self):
        return "Are you sure you want to remove %s as staff member of %s?" % (
            self.operator.releaser.name,
            self.bbs.name,
        )

    def get_html_title(self):
        return "Removing %s as staff member of %s" % (self.operator.releaser.name, self.bbs.name)

    def perform_action(self):
        self.operator.delete()
        description = "Removed %s as staff member of %s" % (self.operator.releaser.name, self.bbs.name)
        Edit.objects.create(
            action_type="remove_bbs_operator",
            focus=self.operator.releaser,
            focus2=self.bbs,
            description=description,
            user=self.request.user,
        )
        self.bbs.updated_at = datetime.datetime.now()
        self.bbs.save(update_fields=["updated_at"])


@writeable_site_required
@login_required
def add_affiliation(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == "POST":
        form = AffiliationForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data["group_nick"].commit().releaser
            affiliation = Affiliation(group=group, bbs=bbs, role=form.cleaned_data["role"])
            affiliation.save()
            if affiliation.role:
                description = "Added BBS %s as %s for %s" % (bbs.name, affiliation.get_role_display(), group.name)
            else:
                description = "Added affiliation with BBS %s for %s" % (bbs.name, group.name)
            Edit.objects.create(
                action_type="add_bbs_affiliation", focus=group, focus2=bbs, description=description, user=request.user
            )
            bbs.updated_at = datetime.datetime.now()
            bbs.save(update_fields=["updated_at"])
            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=affiliations")
    else:
        form = AffiliationForm()

    title = f"Add group affiliation for {bbs.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("bbs_add_affiliation", args=[bbs.id]),
            "submit_button_label": "Add group",
        },
    )


@writeable_site_required
@login_required
def edit_affiliation(request, bbs_id, affiliation_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    affiliation = get_object_or_404(Affiliation, bbs=bbs, id=affiliation_id)

    if request.method == "POST":
        form = AffiliationForm(
            request.POST,
            initial={
                "group_nick": affiliation.group.primary_nick,
                "role": affiliation.role,
            },
        )
        if form.is_valid():
            group = form.cleaned_data["group_nick"].commit().releaser
            affiliation.group = group
            affiliation.role = form.cleaned_data["role"]
            affiliation.save()
            form.log_edit(request.user, affiliation)
            bbs.updated_at = datetime.datetime.now()
            bbs.save(update_fields=["updated_at"])

            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=affiliations")
    else:
        form = AffiliationForm(
            initial={
                "group_nick": affiliation.group.primary_nick,
                "role": affiliation.role,
            }
        )

    title = f"Editing {affiliation.group.name}'s affiliation with {bbs.name}"
    return render(
        request,
        "generic/form.html",
        {
            "form": form,
            "title": title,
            "html_title": title,
            "action_url": reverse("bbs_edit_affiliation", args=[bbs.id, affiliation.id]),
            "submit_button_label": "Update affiliation",
            "delete_url": reverse("bbs_remove_affiliation", args=[bbs.id, affiliation.id]),
            "delete_link_text": "Remove affiliation",
        },
    )


class RemoveAffiliationView(AjaxConfirmationView):
    def get_object(self, request, bbs_id, affiliation_id):
        self.bbs = BBS.objects.get(id=bbs_id)
        self.affiliation = Affiliation.objects.get(bbs=self.bbs, id=affiliation_id)

    def get_redirect_url(self):
        return self.bbs.get_absolute_url() + "?editing=affiliations"

    def get_action_url(self):
        return reverse("bbs_remove_affiliation", args=[self.bbs.id, self.affiliation.id])

    def get_message(self):
        return "Are you sure you want to remove %s's affiliation with %s?" % (
            self.affiliation.group.name,
            self.bbs.name,
        )

    def get_html_title(self):
        return "Removing %s's affiliation with %s" % (self.affiliation.group.name, self.bbs.name)

    def perform_action(self):
        self.affiliation.delete()
        description = "Removed %s's affiliation with %s" % (self.affiliation.group.name, self.bbs.name)
        Edit.objects.create(
            action_type="remove_bbs_affiliation",
            focus=self.affiliation.group,
            focus2=self.bbs,
            description=description,
            user=self.request.user,
        )
        self.bbs.updated_at = datetime.datetime.now()
        self.bbs.save(update_fields=["updated_at"])


class EditTextAdsView(EditTextFilesView):
    subject_model = BBS
    pk_url_kwarg = "bbs_id"
    formset_class = BBSTextAdFormset
    relation_name = "text_ads"
    upload_field_name = "text_ad"
    template_name = "bbs/edit_text_ads.html"
    subject_context_name = "bbs"


@login_required
def text_ad(request, bbs_id, file_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    text_ad = get_object_or_404(TextAd, bbs=bbs, id=file_id)
    fix_encoding_url = (
        reverse("maintenance:fix_bbs_text_ad_encoding", args=(file_id,))
        + "?"
        + urlencode({"return_to": reverse("bbs_text_ad", args=(bbs_id, file_id))})
    )
    return render(
        request,
        "bbs/show_text_ad.html",
        {
            "bbs": bbs,
            "text_ad": text_ad,
            "fix_encoding_url": fix_encoding_url,
        },
    )


class BBSEditTagsView(EditTagsView):
    subject_model = BBS
    pk_url_kwarg = "bbs_id"
    form_class = BBSTagsForm
    action_type = "bbs_edit_tags"


class BBSAddTagView(AddTagView):
    subject_model = BBS
    pk_url_kwarg = "bbs_id"
    action_type = "bbs_add_tag"
    template_name = "bbs/includes/tags_list.html"


class BBSRemoveTagView(RemoveTagView):
    subject_model = BBS
    pk_url_kwarg = "bbs_id"
    action_type = "bbs_remove_tag"
    template_name = "bbs/includes/tags_list.html"


@writeable_site_required
@login_required
def edit_external_links(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == "POST":
        formset = BBSExternalLinkFormSet(request.POST, instance=bbs)
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, "bbs_edit_external_links")

            return HttpResponseRedirect(bbs.get_absolute_url())
    else:
        formset = BBSExternalLinkFormSet(instance=bbs)
    return render(
        request,
        "bbs/edit_external_links.html",
        {
            "bbs": bbs,
            "formset": formset,
        },
    )
