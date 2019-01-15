from __future__ import absolute_import  # ensure that 'from productions.* import...' works relative to the productions app, not views.productions

import datetime
import random

from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from demoscene.shortcuts import get_page
from demoscene.models import Edit
from productions.carousel import Carousel
from productions.models import ProductionType, Production, Byline
from productions.forms import GraphicsIndexFilterForm, ProductionTagsForm, CreateGraphicsForm, ProductionDownloadLinkFormSet
from productions.views.productions import apply_order

from read_only_mode import writeable_site_required

from comments.models import Comment
from comments.forms import CommentForm


def index(request):
	queryset = Production.objects.filter(supertype='graphics')

	order = request.GET.get('order', 'date')
	asc = request.GET.get('dir', 'desc') == 'asc'

	queryset = apply_order(queryset, order, asc)

	form = GraphicsIndexFilterForm(request.GET)

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

	return render(request, 'graphics/index.html', {
		'order': order,
		'production_page': production_page,
		'menu_section': "graphics",
		'asc': asc,
		'form': form,
	})


def show(request, production_id, edit_mode=False):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'graphics':
		return HttpResponseRedirect(production.get_absolute_url())

	if request.user.is_authenticated:
		comment = Comment(commentable=production, user=request.user)
		comment_form = CommentForm(instance=comment, prefix="comment")
		tags_form = ProductionTagsForm(instance=production)
	else:
		comment_form = None
		tags_form = None

	try:
		meta_screenshot = random.choice(production.screenshots.exclude(standard_url=''))
	except IndexError:
		meta_screenshot = None

	return render(request, 'productions/show.html', {
		'production': production,
		'prompt_to_edit': settings.SITE_IS_WRITEABLE and (request.user.is_staff or not production.locked),
		'credits': production.credits_for_listing(),
		'carousel': Carousel(production, request.user),
		'download_links': production.download_links,
		'external_links': production.external_links,
		'info_files': production.info_files.all(),
		'packed_in_productions': [
			pack_member.pack for pack_member in
			production.packed_in.prefetch_related('pack__author_nicks__releaser', 'pack__author_affiliation_nicks__releaser').order_by('pack__release_date_date')
		],
		'tags': production.tags.order_by('name'),
		'blurbs': production.blurbs.all() if request.user.is_staff else None,
		'comment_form': comment_form,
		'tags_form': tags_form,
		'meta_screenshot': meta_screenshot,
	})


def history(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'graphics':
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
