from __future__ import absolute_import, unicode_literals

import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from read_only_mode import writeable_site_required

from demoscene.models import Edit
from productions.forms import CreateGraphicsForm, GraphicsIndexFilterForm, ProductionDownloadLinkFormSet
from productions.models import Byline, Production
from productions.views.generic import HistoryView, IndexView, ShowView


class GraphicsIndexView(IndexView):
    supertype = 'graphics'
    template = 'graphics/index.html'
    filter_form_class = GraphicsIndexFilterForm


class GraphicsShowView(ShowView):
    supertype = 'graphics'

    def get_context_data(self):
        context = super().get_context_data()

        if self.production.can_have_pack_members():
            context['pack_members'] = [
                link.member for link in
                self.production.pack_members.select_related('member').prefetch_related(
                    'member__author_nicks__releaser', 'member__author_affiliation_nicks__releaser'
                )
            ]
        else:
            context['pack_members'] = None

        context['packed_in_productions'] = [
            pack_member.pack for pack_member in
            self.production.packed_in.prefetch_related(
                'pack__author_nicks__releaser', 'pack__author_affiliation_nicks__releaser'
            ).order_by('pack__release_date_date')
        ]

        return context


class GraphicsHistoryView(HistoryView):
    supertype = 'graphics'


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        production = Production(updated_at=datetime.datetime.now())
        form = CreateGraphicsForm(request.POST, instance=production)
        download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
        if form.is_valid() and download_link_formset.is_valid():
            form.save()
            download_link_formset.save_ignoring_uniqueness()
            form.log_creation(request.user)
            return HttpResponseRedirect(production.get_absolute_url())
    else:
        form = CreateGraphicsForm(initial={
            'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
        })
        download_link_formset = ProductionDownloadLinkFormSet()
    return render(request, 'graphics/create.html', {
        'form': form,
        'download_link_formset': download_link_formset,
    })
