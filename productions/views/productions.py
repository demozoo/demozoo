from __future__ import absolute_import  # ensure that 'from productions.* import...' works relative to the productions app, not views.productions

import datetime
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction
from django.db.models import Count
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST

from taggit.models import Tag
from read_only_mode import writeable_site_required
from modal_workflow import render_modal_workflow

from demoscene.shortcuts import get_page, simple_ajax_form, simple_ajax_confirmation, modal_workflow_confirmation
from demoscene.models import Nick, Edit, BlacklistedTag
from productions.forms import ProductionIndexFilterForm, ProductionTagsForm, ProductionEditCoreDetailsForm, GraphicsEditCoreDetailsForm, MusicEditCoreDetailsForm, ProductionInvitationPartyFormset, ProductionEditNotesForm, ProductionBlurbForm, ProductionExternalLinkFormSet, ProductionDownloadLinkFormSet, CreateProductionForm, ProductionCreditedNickForm, ProductionSoundtrackLinkFormset, PackMemberFormset, ProductionInfoFileFormset
from demoscene.forms.common import CreditFormSet
from demoscene.utils.text import slugify_tag
from productions.models import Production, ProductionType, Byline, Credit, Screenshot, ProductionBlurb, InfoFile
from productions.carousel import Carousel

from screenshots.tasks import capture_upload_for_processing
from comments.models import Comment
from comments.forms import CommentForm


def index(request):
    queryset = Production.objects.filter(supertype='production')

    order = request.GET.get('order', 'date')
    asc = request.GET.get('dir', 'desc') == 'asc'

    queryset = apply_order(queryset, order, asc)

    form = ProductionIndexFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data['platform']:
            queryset = queryset.filter(platforms=form.cleaned_data['platform'])
        if form.cleaned_data['production_type']:
            prod_types = ProductionType.get_tree(form.cleaned_data['production_type'])
            queryset = queryset.filter(types__in=prod_types)

    queryset = queryset.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

    production_page = get_page(
        queryset,
        request.GET.get('page', '1'))

    return render(request, 'productions/index.html', {
        'order': order,
        'production_page': production_page,
        'menu_section': "productions",
        'asc': asc,
        'form': form,
    })


def tagged(request, tag_name):
    try:
        tag = Tag.objects.get(name=tag_name)
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
    queryset = Production.objects.filter(tags__name=tag_name).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

    order = request.GET.get('order', 'date')
    asc = request.GET.get('dir', 'desc') == 'asc'

    queryset = apply_order(queryset, order, asc)

    production_page = get_page(
        queryset,
        request.GET.get('page', '1'))

    return render(request, 'productions/tagged.html', {
        'tag': tag,
        'production_page': production_page,
        'order': order,
        'asc': asc,
    })


def apply_order(queryset, order, asc):
    if order == 'title':
        return queryset.order_by('%ssortable_title' % ('' if asc else '-'))
    else:  # date
        if asc:
            return queryset.order_by('release_date_date', 'title')
        else:
            # fiddle order so that empty release dates end up at the end
            return queryset.extra(
                select={'order_date': "coalesce(productions_production.release_date_date, '1970-01-01')"}
            ).order_by('-order_date', '-title')


def show(request, production_id, edit_mode=False):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != 'production':
        return HttpResponseRedirect(production.get_absolute_url())

    if request.user.is_authenticated:
        comment = Comment(commentable=production, user=request.user)
        comment_form = CommentForm(instance=comment, prefix="comment")
        tags_form = ProductionTagsForm(instance=production)
    else:
        comment_form = None
        tags_form = None

    if production.can_have_pack_members():
        pack_members = [
            link.member for link in
            production.pack_members.select_related('member').prefetch_related('member__author_nicks__releaser', 'member__author_affiliation_nicks__releaser')
        ]
    else:
        pack_members = None

    try:
        meta_screenshot = random.choice(production.screenshots.exclude(standard_url=''))
    except IndexError:
        meta_screenshot = None

    return render(request, 'productions/show.html', {
        'production': production,
        'prompt_to_edit': settings.SITE_IS_WRITEABLE and (request.user.is_staff or not production.locked),
        'editing_credits': (request.GET.get('editing') == 'credits'),
        'credits': production.credits_for_listing(),
        'carousel': Carousel(production, request.user),

        'download_links': production.download_links,
        'external_links': production.external_links,
        'info_files': production.info_files.all(),
        'soundtracks': [
            link.soundtrack for link in
            production.soundtrack_links.order_by('position').select_related('soundtrack').prefetch_related('soundtrack__author_nicks__releaser', 'soundtrack__author_affiliation_nicks__releaser')
        ],
        'tags': production.tags.order_by('name'),
        'blurbs': production.blurbs.all() if request.user.is_staff else None,
        'pack_members': pack_members,
        'packed_in_productions': [
            pack_member.pack for pack_member in
            production.packed_in.prefetch_related('pack__author_nicks__releaser', 'pack__author_affiliation_nicks__releaser').order_by('pack__release_date_date')
        ],
        'comment_form': comment_form,
        'tags_form': tags_form,
        'meta_screenshot': meta_screenshot,
    })


def history(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != 'production':
        return HttpResponseRedirect(production.get_history_url())
    return render(request, 'productions/history.html', {
        'production': production,
        'edits': Edit.for_model(production, request.user.is_staff),
    })


@writeable_site_required
@login_required
@transaction.atomic
def edit_core_details(request, production_id):
    production = get_object_or_404(Production, id=production_id)

    if not production.editable_by_user(request.user):
        raise PermissionDenied

    use_invitation_formset = False
    invitation_formset = None

    if production.supertype == 'production':
        form_class = ProductionEditCoreDetailsForm
        use_invitation_formset = True
    elif production.supertype == 'graphics':
        form_class = GraphicsEditCoreDetailsForm
    else:  # production.supertype == 'music':
        form_class = MusicEditCoreDetailsForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=production)

        if use_invitation_formset:
            invitation_formset = ProductionInvitationPartyFormset(request.POST, initial=[
                {'party': party}
                for party in production.invitation_parties.order_by('start_date_date')
            ])

        if form.is_valid() and ((not use_invitation_formset) or invitation_formset.is_valid()):
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            form.save()

            edit_descriptions = []
            main_edit_description = form.changed_data_description
            if main_edit_description:
                edit_descriptions.append(main_edit_description)

            if use_invitation_formset:
                invitation_parties = [party_form.cleaned_data['party'].commit()
                    for party_form in invitation_formset.forms
                    if party_form.cleaned_data.get('party') and party_form not in invitation_formset.deleted_forms]
                production.invitation_parties = invitation_parties

                if invitation_formset.has_changed():
                    party_names = [party.name for party in invitation_parties]
                    if party_names:
                        edit_descriptions.append(
                            u"Set invitation for %s" % (u", ".join(party_names))
                        )
                    else:
                        edit_descriptions.append(u"Unset as invitation")

            if edit_descriptions:
                Edit.objects.create(action_type='edit_production_core_details', focus=production,
                    description=u"; ".join(edit_descriptions), user=request.user)

            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = form_class(instance=production)

        if use_invitation_formset:
            invitation_formset = ProductionInvitationPartyFormset(initial=[
                {'party': party}
                for party in production.invitation_parties.order_by('start_date_date')
            ])

    return render(request, 'productions/edit_core_details.html', {
        'production': production,
        'form': form,
        'invitation_formset': invitation_formset,
    })


@writeable_site_required
@login_required
def edit_notes(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
        title='Editing notes for %s:' % production.title,
        update_datestamp=True, update_bonafide_flag=True, on_success=success)


@writeable_site_required
@login_required
def add_blurb(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())

    blurb = ProductionBlurb(production=production)
    if request.POST:
        form = ProductionBlurbForm(request.POST, instance=blurb)
        if form.is_valid():
            form.save()
            production.has_bonafide_edits = True
            production.save()
            Edit.objects.create(action_type='add_production_blurb', focus=production,
                description="Added blurb", user=request.user, admin_only=True)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = ProductionBlurbForm(instance=blurb)

    return render(request, 'shared/simple_form.html', {
        'form': form,
        'title': 'Adding blurb for %s:' % production.title,
        'html_title': 'Adding blurb for %s' % production.title,
        'action_url': reverse('production_add_blurb', args=[production.id]),
    })


@writeable_site_required
@login_required
def edit_blurb(request, production_id, blurb_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    blurb = get_object_or_404(ProductionBlurb, production=production, id=blurb_id)

    if request.POST:
        form = ProductionBlurbForm(request.POST, instance=blurb)
        if form.is_valid():
            form.save()
            Edit.objects.create(action_type='edit_production_blurb', focus=production,
                description="Edited blurb", user=request.user, admin_only=True)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = ProductionBlurbForm(instance=blurb)

    return render(request, 'productions/edit_blurb_form.html', {
        'form': form,
        'production': production,
        'blurb': blurb,
        'action_url': reverse('production_edit_blurb', args=[production.id, blurb.id]),
    })


@writeable_site_required
@login_required
def delete_blurb(request, production_id, blurb_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    blurb = get_object_or_404(ProductionBlurb, production=production, id=blurb_id)

    if request.method == 'POST':
        if request.POST.get('yes'):
            blurb.delete()
            Edit.objects.create(action_type='delete_production_blurb', focus=production,
                description="Deleted blurb", user=request.user, admin_only=True)
        return HttpResponseRedirect(production.get_absolute_url())
    else:
        return simple_ajax_confirmation(request,
            reverse('production_delete_blurb', args=[production_id, blurb_id]),
            "Are you sure you want to delete this blurb?",
            html_title="Deleting blurb for %s" % production.title)


@writeable_site_required
@login_required
def edit_external_links(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        formset = ProductionExternalLinkFormSet(request.POST, instance=production, queryset=production.links.filter(is_download_link=False))
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, 'production_edit_external_links')
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()

            return HttpResponseRedirect(production.get_absolute_url())
    else:
        formset = ProductionExternalLinkFormSet(instance=production, queryset=production.links.filter(is_download_link=False))
    return render(request, 'productions/edit_links.html', {
        'submit_url': reverse('production_edit_external_links', args=[production.id]),
        'external_or_download': 'external',
        'production': production,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_download_links(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        formset = ProductionDownloadLinkFormSet(request.POST, instance=production, queryset=production.links.filter(is_download_link=True))
        if formset.is_valid():
            formset.save_ignoring_uniqueness()
            formset.log_edit(request.user, 'production_edit_download_links')
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()

            return HttpResponseRedirect(production.get_absolute_url())
    else:
        formset = ProductionDownloadLinkFormSet(instance=production, queryset=production.links.filter(is_download_link=True))
    return render(request, 'productions/edit_links.html', {
        'submit_url': reverse('production_edit_download_links', args=[production.id]),
        'external_or_download': 'download',
        'production': production,
        'formset': formset,
    })


def screenshots(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype == 'music':
        return redirect('production_artwork', production_id)

    screenshots = production.screenshots.order_by('id')

    return render(request, 'productions/screenshots.html', {
        'production': production,
        'screenshots': screenshots,
        'model_label': "Screenshots",
    })


def artwork(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != 'music':
        return redirect('production_screenshots', production_id)
    screenshots = production.screenshots.order_by('id')

    return render(request, 'productions/screenshots.html', {
        'production': production,
        'screenshots': screenshots,
        'model_label': "Artwork",
    })


@writeable_site_required
@login_required
def edit_screenshots(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    if production.supertype == 'music':
        return redirect('production_edit_artwork', production_id)

    return render(request, 'productions/edit_screenshots.html', {
        'production': production,
        'screenshots': production.screenshots.order_by('id'),
        'model_label': 'screenshots',
        'delete_url_name': 'production_delete_screenshot',
    })


@writeable_site_required
@login_required
def edit_artwork(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    if production.supertype != 'music':
        return redirect('production_edit_screenshots', production_id)

    return render(request, 'productions/edit_screenshots.html', {
        'production': production,
        'screenshots': production.screenshots.order_by('id'),
        'model_label': 'artwork',
        'delete_url_name': 'production_delete_artwork',
    })


@writeable_site_required
@login_required
def add_screenshot(request, production_id, is_artwork_view=False):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('screenshot')
        file_count = len(uploaded_files)
        for f in uploaded_files:
            screenshot = Screenshot.objects.create(production=production)
            capture_upload_for_processing(f, screenshot.id)

        if file_count:
            # at least one screenshot was uploaded
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()

            if file_count == 1:
                if is_artwork_view:
                    Edit.objects.create(action_type='add_screenshot', focus=production,
                        description=("Added artwork"), user=request.user)
                else:
                    Edit.objects.create(action_type='add_screenshot', focus=production,
                        description=("Added screenshot"), user=request.user)
            else:
                if is_artwork_view:
                    Edit.objects.create(action_type='add_screenshot', focus=production,
                        description=("Added %s artworks" % file_count), user=request.user)
                else:
                    Edit.objects.create(action_type='add_screenshot', focus=production,
                        description=("Added %s screenshots" % file_count), user=request.user)

        return HttpResponseRedirect(production.get_absolute_url())
    else:
        if is_artwork_view and production.supertype != 'music':
            return redirect('production_add_screenshot', production_id)
        elif not is_artwork_view and production.supertype == 'music':
            return redirect('production_add_artwork', production_id)

    if is_artwork_view:
        return render(request, 'productions/add_artwork.html', {
            'production': production,
        })

    else:
        return render(request, 'productions/add_screenshot.html', {
            'production': production,
        })


@writeable_site_required
@login_required
def delete_screenshot(request, production_id, screenshot_id, is_artwork_view=False):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())

    screenshot = get_object_or_404(Screenshot, id=screenshot_id, production=production)
    if request.method == 'POST':
        if request.POST.get('yes'):
            screenshot.delete()

            # reload production model, as the deletion above may have nullified has_screenshot
            # (which won't be reflected in the existing model instance)
            production = Production.objects.get(pk=production.pk)

            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()
            if is_artwork_view:
                Edit.objects.create(action_type='delete_screenshot', focus=production,
                    description="Deleted artwork", user=request.user)
            else:
                Edit.objects.create(action_type='delete_screenshot', focus=production,
                    description="Deleted screenshot", user=request.user)

        if is_artwork_view:
            return HttpResponseRedirect(reverse('production_edit_artwork', args=[production.id]))
        else:
            return HttpResponseRedirect(reverse('production_edit_screenshots', args=[production.id]))
    else:
        if is_artwork_view:
            if production.supertype != 'music':
                return redirect('production_delete_screenshot', production_id, screenshot_id)

            return simple_ajax_confirmation(request,
                reverse('production_delete_artwork', args=[production_id, screenshot_id]),
                "Are you sure you want to delete this artwork for %s?" % production.title,
                html_title="Deleting artwork for %s" % production.title)
        else:
            if production.supertype == 'music':
                return redirect('production_delete_artwork', production_id, screenshot_id)

            return simple_ajax_confirmation(request,
                reverse('production_delete_screenshot', args=[production_id, screenshot_id]),
                "Are you sure you want to delete this screenshot for %s?" % production.title,
                html_title="Deleting screenshot for %s" % production.title)


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        production = Production(updated_at=datetime.datetime.now())
        form = CreateProductionForm(request.POST, instance=production)
        download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
        if form.is_valid() and download_link_formset.is_valid():
            form.save()
            download_link_formset.save_ignoring_uniqueness()
            form.log_creation(request.user)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = CreateProductionForm(initial={
            'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
        })
        download_link_formset = ProductionDownloadLinkFormSet()
    return render(request, 'productions/create.html', {
        'form': form,
        'download_link_formset': download_link_formset,
    })


@writeable_site_required
@login_required
def add_credit(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        nick_form = ProductionCreditedNickForm(request.POST, production=production)
        credit_formset = CreditFormSet(request.POST, queryset=Credit.objects.none(), prefix="credit")
        if nick_form.is_valid() and credit_formset.is_valid():
            credits = credit_formset.save(commit=False)
            if credits:
                nick = nick_form.cleaned_data['nick'].commit()
                for credit in credits:
                    credit.nick = nick
                    credit.production = production
                    credit.save()
                credits_description = ', '.join([credit.description for credit in credits])
                description = (u"Added credit for %s on %s: %s" % (nick, production, credits_description))
                Edit.objects.create(action_type='add_credit', focus=production,
                    focus2=nick.releaser,
                    description=description, user=request.user)

            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()
            # form.log_creation(request.user)

            return render_credits_update(request, production)
    else:
        nick_form = ProductionCreditedNickForm(production=production)
        credit_formset = CreditFormSet(queryset=Credit.objects.none(), prefix="credit")

    if request.is_ajax():
        return render_modal_workflow(
            request, 'productions/add_credit.html', 'productions/add_credit.js', {
                'production': production,
                'nick_form': nick_form,
                'credit_formset': credit_formset,
            }
        )
    else:
        return render(request, 'productions/add_credit.html', {
            'production': production,
            'nick_form': nick_form,
            'credit_formset': credit_formset,
        })


@writeable_site_required
@login_required
def edit_credit(request, production_id, nick_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    nick = get_object_or_404(Nick, id=nick_id)
    credits = production.credits.filter(nick=nick).extra(
        select={'category_order': "CASE WHEN category = 'Other' THEN 'zzzother' ELSE category END"}
    ).order_by('category_order')
    if request.method == 'POST':
        nick_form = ProductionCreditedNickForm(request.POST, nick=nick, production=production)
        credit_formset = CreditFormSet(request.POST, queryset=credits, prefix="credit")
        if nick_form.is_valid() and credit_formset.is_valid():
            updated_credits = credit_formset.save(commit=False)
            # make sure that each credit has production and nick populated
            for credit in updated_credits:
                credit.nick = nick
                credit.production = production
                credit.save()

            if 'nick' in nick_form.changed_data:
                # need to update the nick field of all credits in the set
                # (not just the ones that have been updated by credit_formset.save)
                nick = nick_form.cleaned_data['nick'].commit()
                credits.update(nick=nick)

            # since we're using commit=False we must manually delete the
            # deleted credits
            for credit in credit_formset.deleted_objects:
                credit.delete()

            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()

            new_credits = Credit.objects.filter(nick=nick, production=production)
            credits_description = ', '.join([credit.description for credit in new_credits])
            Edit.objects.create(action_type='edit_credit', focus=production,
                focus2=nick.releaser,
                description=(u"Updated %s's credit on %s: %s" % (nick, production, credits_description)),
                user=request.user)

            return render_credits_update(request, production)
    else:
        nick_form = ProductionCreditedNickForm(nick=nick, production=production)
        credit_formset = CreditFormSet(queryset=credits, prefix="credit")

    if request.is_ajax():
        return render_modal_workflow(request,
            'productions/edit_credit.html', 'productions/edit_credit.js', {
                'production': production,
                'nick': nick,
                'nick_form': nick_form,
                'credit_formset': credit_formset,
            }
        )
    else:
        return render(request, 'productions/edit_credit.html', {
            'production': production,
            'nick': nick,
            'nick_form': nick_form,
            'credit_formset': credit_formset,
        })


@writeable_site_required
@login_required
def delete_credit(request, production_id, nick_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    nick = get_object_or_404(Nick, id=nick_id)
    if request.method == 'POST':
        if request.POST.get('yes'):
            credits = Credit.objects.filter(nick=nick, production=production)
            if credits:
                credits.delete()
                production.updated_at = datetime.datetime.now()
                production.has_bonafide_edits = True
                production.save()
                Edit.objects.create(action_type='delete_credit', focus=production, focus2=nick.releaser,
                    description=(u"Deleted %s's credit on %s" % (nick, production)), user=request.user)
        return render_credits_update(request, production)
    else:
        return modal_workflow_confirmation(request,
            reverse('production_delete_credit', args=[production_id, nick_id]),
            "Are you sure you want to delete %s's credit from %s?" % (nick.name, production.title),
            html_title="Deleting %s's credit from %s" % (nick.name, production.title))


@writeable_site_required
@login_required
def edit_soundtracks(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        formset = ProductionSoundtrackLinkFormset(request.POST, instance=production)
        if formset.is_valid():
            def form_order_key(form):
                if form.is_valid():
                    return form.cleaned_data['ORDER'] or 9999
                else:
                    return 9999

            sorted_forms = sorted(formset.forms, key=form_order_key)
            for (i, form) in enumerate(sorted_forms):
                form.instance.position = i + 1
            formset.save()
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()
            for stl in production.soundtrack_links.all():
                stl.soundtrack.has_bonafide_edits = True
                stl.soundtrack.save()
            Edit.objects.create(action_type='edit_soundtracks', focus=production,
                description=(u"Edited soundtrack details for %s" % production.title), user=request.user)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        formset = ProductionSoundtrackLinkFormset(instance=production)
    return render(request, 'productions/edit_soundtracks.html', {
        'production': production,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_pack_contents(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        formset = PackMemberFormset(request.POST, instance=production)
        if formset.is_valid():
            def form_order_key(form):
                if form.is_valid():
                    return form.cleaned_data['ORDER'] or 9999
                else:
                    return 9999

            sorted_forms = sorted(formset.forms, key=form_order_key)
            for (i, form) in enumerate(sorted_forms):
                form.instance.position = i + 1
            formset.save()
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True
            production.save()
            for stl in production.pack_members.all():
                stl.member.has_bonafide_edits = True
                stl.member.save()
            Edit.objects.create(action_type='edit_pack_contents', focus=production,
                description=(u"Edited pack contents of %s" % production.title), user=request.user)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        formset = PackMemberFormset(instance=production)
    return render(request, 'productions/edit_pack_contents.html', {
        'production': production,
        'formset': formset,
    })


@writeable_site_required
@login_required
def edit_tags(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    old_tags = set(production.tags.names())
    form = ProductionTagsForm(request.POST, instance=production)
    form.save()
    new_tags = set(production.tags.names())
    if new_tags != old_tags:
        names_string = u', '.join(production.tags.names())
        Edit.objects.create(action_type='production_edit_tags', focus=production,
            description=u"Set tags to %s" % names_string, user=request.user)

        # delete any tags that are now unused
        Tag.objects.annotate(num_prods=Count('taggit_taggeditem_items')).filter(num_prods=0).delete()
    return HttpResponseRedirect(production.get_absolute_url())


@writeable_site_required
@login_required
@require_POST
def add_tag(request, production_id):

    # Only used in AJAX calls.

    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    tag_name = slugify_tag(request.POST.get('tag_name'))

    try:
        blacklisted_tag = BlacklistedTag.objects.get(tag=tag_name)
        tag_name = slugify_tag(blacklisted_tag.replacement)
        message = blacklisted_tag.message
    except BlacklistedTag.DoesNotExist:
        message = None

    if tag_name:
        # check whether it's already present
        existing_tag = production.tags.filter(name=tag_name)
        if not existing_tag:
            production.tags.add(tag_name)
            Edit.objects.create(action_type='production_add_tag', focus=production,
                description=u"Added tag '%s'" % tag_name, user=request.user)

    tags_list_html = render_to_string('productions/_tags_list.html', {
        'tags': production.tags.order_by('name')
    })

    return JsonResponse({
        'tags_list_html': tags_list_html,
        'clean_tag_name': tag_name,
        'message': message,
    })


@writeable_site_required
@login_required
def remove_tag(request, production_id):

    # Only used in AJAX calls.

    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        tag_name = slugify_tag(request.POST.get('tag_name'))
        existing_tag = production.tags.filter(name=tag_name)
        if existing_tag:
            production.tags.remove(tag_name)
            Edit.objects.create(action_type='production_remove_tag', focus=production,
                description=u"Removed tag '%s'" % tag_name, user=request.user)
            if not existing_tag[0].taggit_taggeditem_items.count():
                # no more items use this tag - delete it
                existing_tag[0].delete()

    return render(request, 'productions/_tags_list.html', {
        'tags': production.tags.order_by('name'),
    })


def autocomplete_tags(request):
    tags = Tag.objects.filter(name__istartswith=request.GET.get('term')).order_by('name').values_list('name', flat=True)
    return JsonResponse(list(tags), safe=False)


def autocomplete(request):
    query = request.GET.get('term')
    productions = Production.objects.filter(title__istartswith=query).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')
    supertype = request.GET.get('supertype')
    if supertype:
        productions = productions.filter(supertype=supertype)
    productions = productions[:10]

    production_data = [
        {
            'id': production.id,
            'value': production.title,
            'title': production.title,
            'label': production.title_with_byline,
            'byline': production.byline_string,
            'supertype': production.supertype,
            'platform_name': production.platform_name,
            'production_type_name': production.type_name,
            'url': production.get_absolute_url(),
        }
        for production in productions
    ]
    return JsonResponse(production_data, safe=False)


@writeable_site_required
@login_required
def delete(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())
    if request.method == 'POST':
        if request.POST.get('yes'):
            # insert log entry before actually deleting, so that it doesn't try to
            # insert a null ID for the focus field
            Edit.objects.create(action_type='delete_production', focus=production,
                description=(u"Deleted production '%s'" % production.title), user=request.user)
            production.delete()
            messages.success(request, "'%s' deleted" % production.title)
            return HttpResponseRedirect(reverse('productions'))
        else:
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        return simple_ajax_confirmation(request,
            reverse('delete_production', args=[production_id]),
            "Are you sure you want to delete '%s'?" % production.title,
            html_title="Deleting %s" % production.title)


@writeable_site_required
@login_required
def lock(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not request.user.is_staff:
        return HttpResponseRedirect(production.get_absolute_url())

    if request.method == 'POST':
        if request.POST.get('yes'):
            Edit.objects.create(action_type='lock_production', focus=production,
                description=(u"Protected production '%s'" % production.title), user=request.user)

            production.locked = True
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True

            production.save()
            messages.success(request, "'%s' locked" % production.title)

        return HttpResponseRedirect(production.get_absolute_url())

    else:
        return simple_ajax_confirmation(request,
            reverse('lock_production', args=[production_id]),
            "Locking down a page is a serious decision and shouldn't be done on a whim - "
            "remember that we want to keep Demozoo as open as possible. "
            "Are you absolutely sure you want to lock '%s'?" % production.title,
            html_title="Locking %s" % production.title)


@login_required
def protected(request, production_id):
    production = get_object_or_404(Production, id=production_id)

    if request.user.is_staff and request.method == 'POST':
        if request.POST.get('yes'):
            Edit.objects.create(action_type='unlock_production', focus=production,
                description=(u"Unprotected production '%s'" % production.title), user=request.user)

            production.locked = False
            production.updated_at = datetime.datetime.now()
            production.has_bonafide_edits = True

            production.save()
            messages.success(request, "'%s' unlocked" % production.title)

        return HttpResponseRedirect(production.get_absolute_url())

    else:
        return render(request, 'productions/protected.html', {
            'production': production,
        })


def render_credits_update(request, production):
    if request.is_ajax():
        credits_html = render_to_string('productions/_credits.html', {
            'production': production,
            'credits': production.credits_for_listing(),
            'editing_credits': True,
            'prompt_to_edit': settings.SITE_IS_WRITEABLE and (request.user.is_staff or not production.locked),
        }, request=request)
        return render_modal_workflow(
            request, None, 'productions/edit_credit_done.js', {
                'credits_html': credits_html,
            }
        )
    else:
        return HttpResponseRedirect(production.get_absolute_url() + "?editing=credits#credits_panel")


def carousel(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    carousel = Carousel(production, request.user)
    return HttpResponse(carousel.get_slides_json(), content_type='text/javascript')


@writeable_site_required
@login_required
def edit_info_files(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if not production.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        action_descriptions = []
        all_valid = True

        if request.user.is_staff:  # only staff members can edit/delete existing nfo files
            formset = ProductionInfoFileFormset(request.POST, instance=production)
            all_valid = formset.is_valid()
            if all_valid:
                formset.save()
                if formset.deleted_objects:
                    deleted_files = [info_file.filename for info_file in formset.deleted_objects]
                    if len(deleted_files) > 1:
                        action_descriptions.append(u"Deleted info files: %s" % ", ".join(deleted_files))
                    else:
                        action_descriptions.append(u"Deleted info file %s" % ", ".join(deleted_files))

        if all_valid:
            uploaded_files = request.FILES.getlist('info_file')
            file_count = len(uploaded_files)
            for f in uploaded_files:
                production.info_files.create(file=f)

            if file_count:
                if file_count == 1:
                    action_descriptions.append("Added info file")
                else:
                    action_descriptions.append("Added %s info files" % file_count)

            if action_descriptions:
                # at least one change was made
                action_description = '; '.join(action_descriptions)

                production.updated_at = datetime.datetime.now()
                production.has_bonafide_edits = True
                production.save()

                Edit.objects.create(action_type='edit_info_files', focus=production,
                    description=action_description, user=request.user)

            return HttpResponseRedirect(production.get_absolute_url())

    else:
        formset = ProductionInfoFileFormset(instance=production)

    return render(request, 'productions/edit_info_files.html', {
        'production': production,
        'formset': formset,
        'add_only': (not request.user.is_staff) or (production.info_files.count() == 0),
    })


def info_file(request, production_id, file_id):
    production = get_object_or_404(Production, id=production_id)
    info_file = get_object_or_404(InfoFile, production=production, id=file_id)
    return render(request, 'productions/show_info_file.html', {
        'production': production,
        'info_file': info_file
    })
