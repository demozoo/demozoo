from __future__ import absolute_import, unicode_literals

import datetime
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from read_only_mode import writeable_site_required

from awards.models import Event
from comments.forms import CommentForm
from comments.models import Comment
from demoscene.models import Edit
from demoscene.shortcuts import get_page
from productions.carousel import Carousel
from productions.forms import CreateMusicForm, MusicIndexFilterForm, ProductionDownloadLinkFormSet, ProductionTagsForm
from productions.models import Byline, Production, ProductionType
from productions.views.generic import IndexView, apply_order


class MusicIndexView(IndexView):
    supertype = 'music'
    template = 'music/index.html'
    filter_form_class = MusicIndexFilterForm


def show(request, production_id, edit_mode=False):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != 'music':
        return HttpResponseRedirect(production.get_absolute_url())

    if request.user.is_authenticated:
        comment = Comment(commentable=production, user=request.user)
        comment_form = CommentForm(instance=comment, prefix="comment")
        tags_form = ProductionTagsForm(instance=production)

        awards_accepting_recommendations = [
            (event, event.get_recommendation_options(request.user, production))
            for event in Event.accepting_recommendations_for(production)
        ]
    else:
        comment_form = None
        tags_form = None

        awards_accepting_recommendations = [
            (event, None)
            for event in Event.accepting_recommendations_for(production)
        ]

    try:
        meta_screenshot = random.choice(production.screenshots.exclude(standard_url=''))
    except IndexError:
        meta_screenshot = None

    return render(request, 'productions/show.html', {
        'production': production,
        'prompt_to_edit': settings.SITE_IS_WRITEABLE and (request.user.is_staff or not production.locked),
        'download_links': production.download_links,
        'external_links': production.external_links,
        'info_files': production.info_files.all(),
        'credits': production.credits_for_listing(),
        'carousel': Carousel(production, request.user),
        'featured_in_productions': [
            appearance.production for appearance in
            production.appearances_as_soundtrack.prefetch_related('production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser').order_by('production__release_date_date')
        ],
        'packed_in_productions': [
            pack_member.pack for pack_member in
            production.packed_in.prefetch_related('pack__author_nicks__releaser', 'pack__author_affiliation_nicks__releaser').order_by('pack__release_date_date')
        ],
        'tags': production.tags.order_by('name'),
        'blurbs': production.blurbs.all() if request.user.is_staff else None,
        'comment_form': comment_form,
        'tags_form': tags_form,
        'meta_screenshot': meta_screenshot,
        'awards_accepting_recommendations': awards_accepting_recommendations,
    })


def history(request, production_id):
    production = get_object_or_404(Production, id=production_id)
    if production.supertype != 'music':
        return HttpResponseRedirect(production.get_history_url())
    return render(request, 'productions/history.html', {
        'production': production,
        'edits': Edit.for_model(production, request.user.is_staff),
    })


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        production = Production(updated_at=datetime.datetime.now())
        form = CreateMusicForm(request.POST, instance=production)
        download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
        if form.is_valid() and download_link_formset.is_valid():
            form.save()
            download_link_formset.save_ignoring_uniqueness()
            form.log_creation(request.user)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = CreateMusicForm(initial={
            'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
        })
        download_link_formset = ProductionDownloadLinkFormSet()
    return render(request, 'music/create.html', {
        'form': form,
        'download_link_formset': download_link_formset,
    })
