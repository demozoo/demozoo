from __future__ import absolute_import, unicode_literals

import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from read_only_mode import writeable_site_required

from productions.forms import CreateMusicForm, MusicIndexFilterForm, ProductionDownloadLinkFormSet
from productions.models import Byline, Production
from productions.views.generic import HistoryView, IndexView, ShowView


class MusicIndexView(IndexView):
    supertype = 'music'
    template = 'music/index.html'
    filter_form_class = MusicIndexFilterForm


class MusicShowView(ShowView):
    supertype = 'music'

    def get_context_data(self):
        context = super().get_context_data()

        context['featured_in_productions'] = [
            appearance.production for appearance in
            self.production.appearances_as_soundtrack.prefetch_related(
                'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser'
            ).order_by('production__release_date_date')
        ]
        context['packed_in_productions'] = [
            pack_member.pack for pack_member in
            self.production.packed_in.prefetch_related(
                'pack__author_nicks__releaser', 'pack__author_affiliation_nicks__releaser'
            ).order_by('pack__release_date_date')
        ]

        return context


class MusicHistoryView(HistoryView):
    supertype = 'music'


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
