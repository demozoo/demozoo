import datetime
import re
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from taggit.models import Tag

from common.utils.ajax import request_is_ajax
from common.utils.modal_workflow import render_modal_workflow
from common.utils.pagination import PaginationControls, extract_query_params
from common.views import (
    AddTagView,
    AjaxConfirmationView,
    EditingFormView,
    EditingView,
    EditTagsView,
    EditTextFilesView,
    RemoveTagView,
    UpdateFormView,
    writeable_site_required,
)
from demoscene.forms.common import CreditFormSet
from demoscene.models import Edit, Nick
from demoscene.shortcuts import get_page
from productions.carousel import Carousel
from productions.forms import (
    CreateProductionForm,
    GraphicsEditCoreDetailsForm,
    MusicEditCoreDetailsForm,
    PackMemberFormset,
    ProductionBlurbForm,
    ProductionCreditedNickForm,
    ProductionDownloadLinkFormSet,
    ProductionEditCoreDetailsForm,
    ProductionEditNotesForm,
    ProductionExternalLinkFormSet,
    ProductionIndexFilterForm,
    ProductionInfoFileFormset,
    ProductionInvitationPartyFormset,
    ProductionSoundtrackLinkFormset,
    ProductionTagsForm,
)
from productions.models import Credit, InfoFile, Production, ProductionBlurb, Screenshot
from productions.views.generic import CreateView, HistoryView, IndexView, ShowView, apply_order
from screenshots.tasks import capture_upload_for_processing


class ProductionIndexView(IndexView):
    supertype = "production"
    template = "productions/index.html"
    filter_form_class = ProductionIndexFilterForm
    url_name = "productions"


def tagged(request, tag_name):
    try:
        tag = Tag.objects.get(name=tag_name)
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
    queryset = Production.objects.filter(tags__name=tag_name).prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser", "platforms", "types"
    )

    order = request.GET.get("order", "date")
    asc = request.GET.get("dir", "desc") == "asc"

    queryset = apply_order(queryset, order, asc)

    production_page = get_page(queryset, request.GET.get("page", "1"))

    return render(
        request,
        "productions/tagged.html",
        {
            "tag": tag,
            "production_page": production_page,
            "order": order,
            "asc": asc,
            "pagination_controls": PaginationControls(
                production_page,
                reverse("productions_tagged", args=[tag_name]),
                extract_query_params(request.GET, ["order", "dir"]),
            ),
        },
    )


class ProductionShowView(ShowView):
    supertype = "production"

    def get_context_data(self):
        context = super().get_context_data()

        if self.production.can_have_pack_members():
            context["pack_members"] = [
                link.member
                for link in self.production.pack_members.select_related("member").prefetch_related(
                    "member__author_nicks__releaser", "member__author_affiliation_nicks__releaser"
                )
            ]
        else:
            context["pack_members"] = None

        context["soundtracks"] = [
            link.soundtrack
            for link in self.production.soundtrack_links.order_by("position")
            .select_related("soundtrack")
            .prefetch_related("soundtrack__author_nicks__releaser", "soundtrack__author_affiliation_nicks__releaser")
        ]
        context["packed_in_productions"] = [
            pack_member.pack
            for pack_member in self.production.packed_in.prefetch_related(
                "pack__author_nicks__releaser", "pack__author_affiliation_nicks__releaser"
            ).order_by("pack__release_date_date")
        ]

        return context


class ProductionHistoryView(HistoryView):
    supertype = "production"


class EditCoreDetailsView(EditingView):
    template_name = "productions/edit_core_details.html"

    def get_login_return_url(self):
        # Instead of redirecting back to this edit form after login, redirect to the production page.
        # This is because the 'edit' button pointing here is the only one that non-logged-in users
        # see, and thus it's the one they'll click on even if the thing they want to edit is something
        # else on the page. Taking them back to the production page will give them the full complement
        # of edit buttons, allowing them to locate the one they actually want.
        return reverse("production", args=[self.kwargs["production_id"]])

    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def prepare(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)

        if not self.production.editable_by_user(request.user):
            raise PermissionDenied

        self.use_invitation_formset = False
        self.invitation_formset = None

        if self.production.supertype == "production":
            self.form_class = ProductionEditCoreDetailsForm
            self.use_invitation_formset = True
        elif self.production.supertype == "graphics":
            self.form_class = GraphicsEditCoreDetailsForm
        else:  # self.production.supertype == 'music':
            self.form_class = MusicEditCoreDetailsForm

    def post(self, request, production_id):
        self.form = self.form_class(request.POST, instance=self.production)

        if self.use_invitation_formset:
            self.invitation_formset = ProductionInvitationPartyFormset(
                request.POST,
                initial=[{"party": party} for party in self.production.invitation_parties.order_by("start_date_date")],
            )

        if self.form.is_valid() and ((not self.use_invitation_formset) or self.invitation_formset.is_valid()):
            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.form.save()

            edit_descriptions = []
            main_edit_description = self.form.changed_data_description
            if main_edit_description:
                edit_descriptions.append(main_edit_description)

            if self.use_invitation_formset:
                invitation_parties = [
                    party_form.cleaned_data["party"].commit()
                    for party_form in self.invitation_formset.forms
                    if party_form.cleaned_data.get("party") and party_form not in self.invitation_formset.deleted_forms
                ]
                self.production.invitation_parties.set(invitation_parties)

                if self.invitation_formset.has_changed():
                    party_names = [party.name for party in invitation_parties]
                    if party_names:
                        edit_descriptions.append("Set invitation for %s" % (", ".join(party_names)))
                    else:
                        edit_descriptions.append("Unset as invitation")

            if edit_descriptions:
                Edit.objects.create(
                    action_type="edit_production_core_details",
                    focus=self.production,
                    description="; ".join(edit_descriptions),
                    user=request.user,
                )

            return HttpResponseRedirect(self.production.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, production_id):
        self.form = self.form_class(instance=self.production)

        if self.use_invitation_formset:
            self.invitation_formset = ProductionInvitationPartyFormset(
                initial=[{"party": party} for party in self.production.invitation_parties.order_by("start_date_date")]
            )

        return self.render_to_response()

    def get_title(self):
        return f"Editing {self.production.supertype}: {self.production.title}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "production": self.production,
                "form": self.form,
                "invitation_formset": self.invitation_formset,
                "action_url": reverse("production_edit_core_details", args=[self.production.id]),
            }
        )
        return context


class EditNotesView(UpdateFormView):
    form_class = ProductionEditNotesForm
    action_url_name = "production_edit_notes"
    update_bonafide_flag = True
    update_datestamp = True

    def get_object(self):
        return get_object_or_404(Production, id=self.kwargs["production_id"])

    def can_edit(self, object):
        return self.request.user.is_staff

    def get_title(self):
        return "Editing notes for %s:" % self.object.title


class AddBlurbView(EditingFormView):
    form_class = ProductionBlurbForm

    def get_object(self):
        return get_object_or_404(Production, id=self.kwargs["production_id"])

    def check_permission(self):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(self.object.get_absolute_url())

    def get_form_kwargs(self):
        return {"instance": ProductionBlurb(production=self.object)}

    def form_valid(self):
        self.form.save()
        self.object.has_bonafide_edits = True
        self.object.save()
        Edit.objects.create(
            action_type="add_production_blurb",
            focus=self.object,
            description="Added blurb",
            user=self.request.user,
            admin_only=True,
        )

    def get_title(self):
        return "Adding blurb for %s:" % self.object.title

    def get_action_url(self):
        return reverse("production_add_blurb", args=[self.object.id])


class EditBlurbView(EditingView):
    def prepare(self, request, production_id, blurb_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not request.user.is_staff:
            return HttpResponseRedirect(self.production.get_absolute_url())
        self.blurb = get_object_or_404(ProductionBlurb, production=self.production, id=blurb_id)

    def post(self, request, production_id, blurb_id):
        self.form = ProductionBlurbForm(request.POST, instance=self.blurb)
        if self.form.is_valid():
            self.form.save()
            Edit.objects.create(
                action_type="edit_production_blurb",
                focus=self.production,
                description="Edited blurb",
                user=request.user,
                admin_only=True,
            )
            return HttpResponseRedirect(self.production.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, production_id, blurb_id):
        self.form = ProductionBlurbForm(instance=self.blurb)
        return self.render_to_response()

    def get_title(self):
        return f"Editing blurb for {self.production.title}"

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "form": self.form,
                "action_url": reverse("production_edit_blurb", args=[self.production.id, self.blurb.id]),
                "submit_button_label": "Update blurb",
                "delete_url": reverse("production_delete_blurb", args=[self.production.id, self.blurb.id]),
                "delete_link_text": "Delete this blurb",
            }
        )
        return context


class DeleteBlurbView(AjaxConfirmationView):
    def get_object(self, request, production_id, blurb_id):
        self.production = Production.objects.get(id=production_id)
        self.blurb = ProductionBlurb.objects.get(id=blurb_id, production=self.production)

    def is_permitted(self):
        return self.request.user.is_staff

    def get_redirect_url(self):
        return self.production.get_absolute_url()

    def get_action_url(self):
        return reverse("production_delete_blurb", args=[self.production.id, self.blurb.id])

    def get_message(self):
        return "Are you sure you want to delete this blurb?"

    def get_html_title(self):
        return "Deleting blurb for %s" % self.production.title

    def perform_action(self):
        self.blurb.delete()
        Edit.objects.create(
            action_type="delete_production_blurb",
            focus=self.production,
            description="Deleted blurb",
            user=self.request.user,
            admin_only=True,
        )


class EditLinksView(EditingView):
    template_name = "productions/edit_links.html"

    def prepare(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied

    def post(self, request, production_id):
        self.formset = self.formset_class(
            request.POST,
            instance=self.production,
            queryset=self.production.links.filter(is_download_link=self.is_download_link),
        )
        if self.formset.is_valid():
            self.formset.save_ignoring_uniqueness()
            self.formset.log_edit(request.user, self.log_action_type)
            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()

            return HttpResponseRedirect(self.production.get_absolute_url())
        else:
            return self.render_to_response()

    def get(self, request, production_id):
        self.formset = self.formset_class(
            instance=self.production, queryset=self.production.links.filter(is_download_link=self.is_download_link)
        )
        return self.render_to_response()

    def get_context_data(self):
        context = super().get_context_data()
        context.update(
            {
                "action_url": reverse(self.action_url_name, args=[self.production.id]),
                "formset": self.formset,
                "submit_button_label": "Update links",
            }
        )
        return context


class EditExternalLinksView(EditLinksView):
    formset_class = ProductionExternalLinkFormSet
    is_download_link = False
    log_action_type = "production_edit_external_links"
    action_url_name = "production_edit_external_links"

    def get_title(self):
        return f"Editing external links for {self.production.title}"


class EditDownloadLinksView(EditLinksView):
    formset_class = ProductionDownloadLinkFormSet
    is_download_link = True
    log_action_type = "production_edit_download_links"
    action_url_name = "production_edit_download_links"

    def get_title(self):
        return f"Editing download links for {self.production.title}"


def screenshots(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype == "music":
        return redirect("production_artwork", production_id)

    screenshots = production.screenshots.order_by("id")

    return render(
        request,
        "productions/screenshots.html",
        {
            "production": production,
            "screenshots": screenshots,
            "model_label": "Screenshots",
        },
    )


def artwork(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != "music":
        return redirect("production_screenshots", production_id)
    screenshots = production.screenshots.order_by("id")

    return render(
        request,
        "productions/screenshots.html",
        {
            "production": production,
            "screenshots": screenshots,
            "model_label": "Artwork",
        },
    )


@writeable_site_required
@login_required
def edit_screenshots(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    if production.supertype == "music":
        return redirect("production_edit_artwork", production_id)

    return render(
        request,
        "productions/edit_screenshots.html",
        {
            "production": production,
            "screenshots": production.screenshots.order_by("id"),
            "model_label": "screenshots",
            "delete_url_name": "production_delete_screenshot",
        },
    )


@writeable_site_required
@login_required
def edit_artwork(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    if production.supertype != "music":
        return redirect("production_edit_screenshots", production_id)

    return render(
        request,
        "productions/edit_screenshots.html",
        {
            "production": production,
            "screenshots": production.screenshots.order_by("id"),
            "model_label": "artwork",
            "delete_url_name": "production_delete_artwork",
        },
    )


class AddScreenshotView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, production_id, is_artwork_view=False):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied

        self.is_artwork_view = is_artwork_view
        return super().dispatch(request, production_id)

    def post(self, request, production_id):
        uploaded_files = request.FILES.getlist("screenshot")
        file_count = len(uploaded_files)
        for f in uploaded_files:
            screenshot = Screenshot.objects.create(production=self.production)
            capture_upload_for_processing(f, screenshot.id)

        if file_count:
            # at least one screenshot was uploaded
            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()

            if file_count == 1:
                if self.is_artwork_view:
                    Edit.objects.create(
                        action_type="add_screenshot",
                        focus=self.production,
                        description=("Added artwork"),
                        user=request.user,
                    )
                else:
                    Edit.objects.create(
                        action_type="add_screenshot",
                        focus=self.production,
                        description=("Added screenshot"),
                        user=request.user,
                    )
            else:
                if self.is_artwork_view:
                    Edit.objects.create(
                        action_type="add_screenshot",
                        focus=self.production,
                        description=("Added %s artworks" % file_count),
                        user=request.user,
                    )
                else:
                    Edit.objects.create(
                        action_type="add_screenshot",
                        focus=self.production,
                        description=("Added %s screenshots" % file_count),
                        user=request.user,
                    )

        return HttpResponseRedirect(self.production.get_absolute_url())

    def get(self, request, production_id):
        if self.is_artwork_view and self.production.supertype != "music":
            return redirect("production_add_screenshot", production_id)
        elif not self.is_artwork_view and self.production.supertype == "music":
            return redirect("production_add_artwork", production_id)

        return self.render_to_response(request)

    def render_to_response(self, request):
        if self.is_artwork_view:
            title = f"Adding artwork for {self.production.title}"
            return render(
                request,
                "productions/add_artwork.html",
                {
                    "production": self.production,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_add_artwork", args=[self.production.id]),
                    "submit_button_label": "Add artwork",
                },
            )

        else:
            title = f"Adding screenshots for {self.production.title}"
            return render(
                request,
                "productions/add_screenshot.html",
                {
                    "production": self.production,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_add_screenshot", args=[self.production.id]),
                    "submit_button_label": "Add screenshot",
                },
            )


class DeleteScreenshotView(AjaxConfirmationView):
    log_description = "Deleted screenshot"

    def get_object(self, request, production_id, screenshot_id):
        self.production = Production.objects.get(id=production_id)
        self.screenshot = Screenshot.objects.get(id=screenshot_id, production=self.production)

    def validate(self):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(self.production.get_absolute_url())

        if self.production.supertype == "music":
            return redirect("production_delete_artwork", self.production.id, self.screenshot.id)

    def perform_action(self):
        self.screenshot.delete()

        # reload production model, as the deletion above may have nullified has_screenshot
        # (which won't be reflected in the existing model instance)
        self.production = Production.objects.get(pk=self.production.pk)

        self.production.updated_at = datetime.datetime.now()
        self.production.has_bonafide_edits = True
        self.production.save()

        Edit.objects.create(
            action_type="delete_screenshot",
            focus=self.production,
            description=self.log_description,
            user=self.request.user,
        )

    def get_redirect_url(self):
        return reverse("production_edit_screenshots", args=[self.production.id])

    def get_message(self):
        return "Are you sure you want to delete this screenshot for %s?" % self.production.title

    def get_html_title(self):
        return "Deleting screenshot for %s" % self.production.title

    def get_action_url(self):
        return reverse("production_delete_screenshot", args=[self.production.id, self.screenshot.id])


class DeleteArtworkView(DeleteScreenshotView):
    log_description = "Deleted artwork"

    def validate(self):
        if not self.request.user.is_staff:
            return HttpResponseRedirect(self.production.get_absolute_url())

        if self.production.supertype != "music":
            return redirect("production_delete_screenshot", self.production.id, self.screenshot.id)

    def get_redirect_url(self):
        return reverse("production_edit_artwork", args=[self.production.id])

    def get_message(self):
        return "Are you sure you want to delete this artwork for %s?" % self.production.title

    def get_html_title(self):
        return "Deleting artwork for %s" % self.production.title

    def get_action_url(self):
        return reverse("production_delete_artwork", args=[self.production.id, self.screenshot.id])


class CreateProductionView(CreateView):
    form_class = CreateProductionForm
    template = "productions/create.html"
    title = "New production"
    action_url_name = "new_production"
    submit_button_label = "Add new production"


class AddCreditView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied

        return super().dispatch(request, production_id)

    def post(self, request, production_id):
        self.nick_form = ProductionCreditedNickForm(request.POST, production=self.production)
        self.credit_formset = CreditFormSet(request.POST, queryset=Credit.objects.none(), prefix="credit")
        if self.nick_form.is_valid() and self.credit_formset.is_valid():
            credits = self.credit_formset.save(commit=False)
            if credits:
                nick = self.nick_form.cleaned_data["nick"].commit()
                for credit in credits:
                    credit.nick = nick
                    credit.production = self.production
                    credit.save()
                credits_description = ", ".join([credit.description for credit in credits])
                description = "Added credit for %s on %s: %s" % (nick, self.production, credits_description)
                Edit.objects.create(
                    action_type="add_credit",
                    focus=self.production,
                    focus2=nick.releaser,
                    description=description,
                    user=request.user,
                )

            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()

            return render_credits_update(request, self.production)
        else:
            return self.render_to_response(request)

    def get(self, request, production_id):
        self.nick_form = ProductionCreditedNickForm(production=self.production)
        self.credit_formset = CreditFormSet(queryset=Credit.objects.none(), prefix="credit")
        return self.render_to_response(request)

    def render_to_response(self, request):
        title = f"Adding credit for {self.production.title}"
        if request_is_ajax(request):
            return render_modal_workflow(
                request,
                "productions/add_credit.html",
                {
                    "production": self.production,
                    "nick_form": self.nick_form,
                    "credit_formset": self.credit_formset,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_add_credit", args=[self.production.id]),
                    "submit_button_label": "Add credit",
                },
                json_data={"step": "form"},
            )
        else:
            return render(
                request,
                "productions/add_credit.html",
                {
                    "production": self.production,
                    "nick_form": self.nick_form,
                    "credit_formset": self.credit_formset,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_add_credit", args=[self.production.id]),
                    "submit_button_label": "Add credit",
                },
            )


class EditCreditView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, production_id, nick_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied
        self.nick = get_object_or_404(Nick, id=nick_id)
        self.credits = (
            self.production.credits.filter(nick=self.nick)
            .extra(select={"category_order": "CASE WHEN category = 'Other' THEN 'zzzother' ELSE category END"})
            .order_by("category_order")
        )
        return super().dispatch(request, production_id, nick_id)

    def post(self, request, production_id, nick_id):
        self.nick_form = ProductionCreditedNickForm(request.POST, nick=self.nick, production=self.production)
        self.credit_formset = CreditFormSet(request.POST, queryset=self.credits, prefix="credit")
        if self.nick_form.is_valid() and self.credit_formset.is_valid():
            updated_credits = self.credit_formset.save(commit=False)
            # make sure that each credit has production and nick populated
            for credit in updated_credits:
                credit.nick = self.nick
                credit.production = self.production
                credit.save()

            if "nick" in self.nick_form.changed_data:
                # need to update the nick field of all credits in the set
                # (not just the ones that have been updated by self.credit_formset.save)
                self.nick = self.nick_form.cleaned_data["nick"].commit()
                self.credits.update(nick=self.nick)

            # since we're using commit=False we must manually delete the
            # deleted credits
            for credit in self.credit_formset.deleted_objects:
                credit.delete()

            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()

            new_credits = Credit.objects.filter(nick=self.nick, production=self.production)
            credits_description = ", ".join([credit.description for credit in new_credits])
            Edit.objects.create(
                action_type="edit_credit",
                focus=self.production,
                focus2=self.nick.releaser,
                description=("Updated %s's credit on %s: %s" % (self.nick, self.production, credits_description)),
                user=request.user,
            )

            return render_credits_update(request, self.production)
        else:
            return self.render_to_response(request)

    def get(self, request, production_id, nick_id):
        self.nick_form = ProductionCreditedNickForm(nick=self.nick, production=self.production)
        self.credit_formset = CreditFormSet(queryset=self.credits, prefix="credit")
        return self.render_to_response(request)

    def render_to_response(self, request):
        title = f"Editing credit for {self.production.title}"

        if request_is_ajax(request):
            return render_modal_workflow(
                request,
                "productions/edit_credit.html",
                {
                    "production": self.production,
                    "nick": self.nick,
                    "nick_form": self.nick_form,
                    "credit_formset": self.credit_formset,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_edit_credit", args=[self.production.id, self.nick.id]),
                    "submit_button_label": "Update credit",
                },
                json_data={"step": "form"},
            )
        else:
            return render(
                request,
                "productions/edit_credit.html",
                {
                    "production": self.production,
                    "nick": self.nick,
                    "nick_form": self.nick_form,
                    "credit_formset": self.credit_formset,
                    "title": title,
                    "html_title": title,
                    "action_url": reverse("production_edit_credit", args=[self.production.id, self.nick.id]),
                    "submit_button_label": "Update credit",
                },
            )


@writeable_site_required
@login_required
def delete_credit(request, production_id, nick_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    nick = get_object_or_404(Nick, id=nick_id)
    if request.method == "POST":
        if request.POST.get("yes"):
            credits = Credit.objects.filter(nick=nick, production=production)
            if credits:
                credits.delete()
                production.updated_at = datetime.datetime.now()
                production.has_bonafide_edits = True
                production.save()
                Edit.objects.create(
                    action_type="delete_credit",
                    focus=production,
                    focus2=nick.releaser,
                    description=("Deleted %s's credit on %s" % (nick, production)),
                    user=request.user,
                )
        return render_credits_update(request, production)
    else:
        return render_modal_workflow(
            request,
            "generic/simple_confirmation.html",
            {
                "html_title": "Deleting %s's credit from %s" % (nick.name, production.title),
                "message": "Are you sure you want to delete %s's credit from %s?" % (nick.name, production.title),
                "action_url": reverse("production_delete_credit", args=[production_id, nick_id]),
            },
            json_data={"step": "confirm"},
        )


class EditSoundtracksView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied

        return super().dispatch(request, production_id)

    def post(self, request, production_id):
        self.formset = ProductionSoundtrackLinkFormset(request.POST, instance=self.production)
        if self.formset.is_valid():

            def form_order_key(form):
                if form.is_valid():
                    return form.cleaned_data["ORDER"] or 9999
                else:
                    return 9999

            sorted_forms = sorted(self.formset.forms, key=form_order_key)
            for i, form in enumerate(sorted_forms):
                form.instance.position = i + 1
            self.formset.save()
            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()
            for stl in self.production.soundtrack_links.all():
                stl.soundtrack.has_bonafide_edits = True
                stl.soundtrack.save()
            Edit.objects.create(
                action_type="edit_soundtracks",
                focus=self.production,
                description=("Edited soundtrack details for %s" % self.production.title),
                user=request.user,
            )
            return HttpResponseRedirect(self.production.get_absolute_url())
        else:
            return self.render_to_response(request)

    def get(self, request, production_id):
        self.formset = ProductionSoundtrackLinkFormset(instance=self.production)
        return self.render_to_response(request)

    def render_to_response(self, request):
        title = f"Editing soundtrack details for {self.production.title}"
        return render(
            request,
            "productions/edit_soundtracks.html",
            {
                "production": self.production,
                "formset": self.formset,
                "title": title,
                "html_title": title,
                "action_url": reverse("production_edit_soundtracks", args=[self.production.id]),
                "submit_button_label": "Update soundtracks",
            },
        )


class EditPackContentsView(View):
    @method_decorator(writeable_site_required)
    @method_decorator(login_required)
    def dispatch(self, request, production_id):
        self.production = get_object_or_404(Production, id=production_id)
        if not self.production.editable_by_user(request.user):
            raise PermissionDenied
        return super().dispatch(request, production_id)

    def post(self, request, production_id):
        self.formset = PackMemberFormset(request.POST, instance=self.production)
        if self.formset.is_valid():

            def form_order_key(form):
                if form.is_valid():
                    return form.cleaned_data["ORDER"] or 9999
                else:
                    return 9999

            sorted_forms = sorted(self.formset.forms, key=form_order_key)
            for i, form in enumerate(sorted_forms):
                form.instance.position = i + 1
            self.formset.save()
            self.production.updated_at = datetime.datetime.now()
            self.production.has_bonafide_edits = True
            self.production.save()
            for stl in self.production.pack_members.all():
                stl.member.has_bonafide_edits = True
                stl.member.save()
            Edit.objects.create(
                action_type="edit_pack_contents",
                focus=self.production,
                description=("Edited pack contents of %s" % self.production.title),
                user=request.user,
            )
            return HttpResponseRedirect(self.production.get_absolute_url())
        else:
            return self.render_to_response(request)

    def get(self, request, production_id):
        self.formset = PackMemberFormset(instance=self.production)
        return self.render_to_response(request)

    def render_to_response(self, request):
        title = f"Editing pack contents for {self.production.title}"
        return render(
            request,
            "productions/edit_pack_contents.html",
            {
                "production": self.production,
                "formset": self.formset,
                "title": title,
                "html_title": title,
                "action_url": reverse("production_edit_pack_contents", args=[self.production.id]),
                "submit_button_label": "Update pack contents",
            },
        )


class ProductionEditTagsView(EditTagsView):
    subject_model = Production
    pk_url_kwarg = "production_id"
    form_class = ProductionTagsForm
    action_type = "production_edit_tags"

    def can_edit(self, subject):
        return subject.editable_by_user(self.request.user)


class ProductionAddTagView(AddTagView):
    subject_model = Production
    pk_url_kwarg = "production_id"
    action_type = "production_add_tag"
    template_name = "productions/includes/tags_list.html"

    def can_edit(self, subject):
        return subject.editable_by_user(self.request.user)


class ProductionRemoveTagView(RemoveTagView):
    subject_model = Production
    pk_url_kwarg = "production_id"
    action_type = "production_remove_tag"
    template_name = "productions/includes/tags_list.html"

    def can_edit(self, subject):
        return subject.editable_by_user(self.request.user)


def autocomplete_tags(request):
    term = request.GET.get("term", "hello I am a shitty web crawler that strips out query parameters")
    tags = Tag.objects.filter(name__istartswith=term).order_by("name").values_list("name", flat=True)
    return JsonResponse(list(tags), safe=False)


def autocomplete(request):
    term = request.GET.get("term")
    query = Q(title__istartswith=term)
    if term.isdigit():
        query |= Q(id=int(term))
    elif match := re.search(r"/(?:productions|music|graphics)/(\d+)/$", term):
        query |= Q(id=int(match.group(1)))

    productions = Production.objects.filter(query).prefetch_related(
        "author_nicks__releaser", "author_affiliation_nicks__releaser"
    )
    supertype = request.GET.get("supertype")
    if supertype:
        productions = productions.filter(supertype=supertype)
    productions = productions[:10]

    production_data = [
        {
            "id": production.id,
            "value": production.title,
            "title": production.title,
            "label": production.title_with_byline,
            "byline": production.byline_string,
            "supertype": production.supertype,
            "platform_name": production.platform_name,
            "production_type_name": production.type_name,
            "url": production.get_absolute_url(),
        }
        for production in productions
    ]
    return JsonResponse(production_data, safe=False)


class DeleteProductionView(AjaxConfirmationView):
    html_title = "Deleting %s"
    message = "Are you sure you want to delete %s?"
    action_url_path = "delete_production"

    def get_object(self, request, production_id):
        return Production.objects.get(id=production_id)

    def is_permitted(self):
        return self.request.user.is_staff

    def get_redirect_url(self):
        return reverse("productions")

    def get_cancel_url(self):
        return self.object.get_absolute_url()

    def perform_action(self):
        # insert log entry before actually deleting, so that it doesn't try to
        # insert a null ID for the focus field
        Edit.objects.create(
            action_type="delete_production",
            focus=self.object,
            description=("Deleted production '%s'" % self.object.title),
            user=self.request.user,
        )
        self.object.delete()
        messages.success(self.request, "'%s' deleted" % self.object.title)


class LockProductionView(AjaxConfirmationView):
    html_title = "Locking %s"
    message = (
        "Locking down a page is a serious decision and shouldn't be done on a whim - "
        "remember that we want to keep Demozoo as open as possible. "
        "Are you absolutely sure you want to lock '%s'?"
    )
    action_url_path = "lock_production"

    def is_permitted(self):  # pragma: no cover
        return self.request.user.is_staff

    def get_object(self, request, production_id):
        return Production.objects.get(id=production_id)

    def perform_action(self):  # pragma: no cover
        Edit.objects.create(
            action_type="lock_production",
            focus=self.object,
            description=("Protected production '%s'" % self.object.title),
            user=self.request.user,
        )

        self.object.locked = True
        self.object.updated_at = datetime.datetime.now()
        self.object.has_bonafide_edits = True

        self.object.save()
        messages.success(self.request, "'%s' locked" % self.object.title)


@login_required
def protected(request, production_id):
    production = get_object_or_404(Production, id=production_id)

    if request.user.is_staff and request.method == "POST":
        if request.POST.get("yes"):
            Edit.objects.create(
                action_type="unlock_production",
                focus=production,
                description=("Unprotected production '%s'" % production.title),
                user=request.user,
            )

            production.locked = False
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True

            production.save()
            messages.success(request, "'%s' unlocked" % production.title)

        return HttpResponseRedirect(production.get_absolute_url())

    else:
        return render(
            request,
            "productions/protected.html",
            {
                "production": production,
            },
        )


def render_credits_update(request, production):
    if request_is_ajax(request):
        prompt_to_edit = settings.SITE_IS_WRITEABLE and (request.user.is_staff or not production.locked)
        can_edit = prompt_to_edit and request.user.is_authenticated

        credits_html = render_to_string(
            "productions/includes/credits_panel.html",
            {
                "production": production,
                "credits": production.credits_for_listing(),
                "is_editing": True,
                "prompt_to_edit": prompt_to_edit,
                "can_edit": can_edit,
            },
            request=request,
        )
        return render_modal_workflow(
            request,
            None,
            json_data={
                "step": "done",
                "panel_html": credits_html,
            },
        )
    else:
        return HttpResponseRedirect(production.get_absolute_url() + "?editing=credits#credits_panel")


def carousel(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    carousel = Carousel(production, request.user)
    return HttpResponse(carousel.get_slides_json(), content_type="text/javascript")


class EditInfoFilesView(EditTextFilesView):
    subject_model = Production
    pk_url_kwarg = "production_id"
    formset_class = ProductionInfoFileFormset
    relation_name = "info_files"
    upload_field_name = "info_file"
    template_name = "productions/edit_info_files.html"
    subject_context_name = "production"
    action_url_name = "production_edit_info_files"
    add_button_label = "Add info file"
    update_button_label = "Update info files"

    def can_edit(self, subject):
        return subject.editable_by_user(self.request.user)

    def mark_as_edited(self, subject):
        subject.updated_at = datetime.datetime.now()
        subject.has_bonafide_edits = True
        subject.save()

    def get_title(self):
        if self.add_only:
            return f"Adding info file for {self.subject.title}"
        else:
            return f"Editing info files for {self.subject.title}"


@login_required
def info_file(request, production_id, file_id):
    production = get_object_or_404(Production, id=production_id)
    info_file = get_object_or_404(InfoFile, production=production, id=file_id)
    fix_encoding_url = (
        reverse("maintenance:fix_prod_info_file_encoding", args=(info_file.id,))
        + "?"
        + urlencode({"return_to": reverse("production_info_file", args=(production_id, file_id))})
    )
    return render(
        request,
        "productions/show_info_file.html",
        {
            "production": production,
            "info_file": info_file,
            "fix_encoding_url": fix_encoding_url,
        },
    )
