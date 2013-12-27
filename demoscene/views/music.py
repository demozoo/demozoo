from demoscene.shortcuts import *
from demoscene.models import Production, Byline
from demoscene.forms.production import *

from demoscene.views.productions import apply_order


from django.contrib.auth.decorators import login_required
import datetime
from read_only_mode import writeable_site_required

from comments.models import ProductionComment
from comments.forms import ProductionCommentForm


def index(request):
	queryset = Production.objects.filter(supertype='music').select_related('default_screenshot').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')

	order = request.GET.get('order', 'title')
	asc = request.GET.get('dir', 'asc') == 'asc'

	queryset = apply_order(queryset, order, asc)

	form = MusicIndexFilterForm(request.GET)

	if form.is_valid():
		if form.cleaned_data['platform']:
			queryset = queryset.filter(platforms=form.cleaned_data['platform'])
		if form.cleaned_data['production_type']:
			prod_types = ProductionType.get_tree(form.cleaned_data['production_type'])
			queryset = queryset.filter(types__in=prod_types)

	production_page = get_page(
		queryset,
		request.GET.get('page', '1'))

	return render(request, 'music/index.html', {
		'order': order,
		'production_page': production_page,
		'menu_section': "music",
		'asc': asc,
		'form': form,
	})


def show(request, production_id, edit_mode=False):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'music':
		return HttpResponseRedirect(production.get_absolute_url())

	if request.user.is_authenticated():
		comment = ProductionComment(production=production, user=request.user)
		comment_form = ProductionCommentForm(instance=comment, prefix="comment")
	else:
		comment_form = None

	return render(request, 'productions/show.html', {
		'production': production,
		'download_links': production.links.filter(is_download_link=True),
		'external_links': production.links.filter(is_download_link=False),
		'credits': production.credits.select_related('nick__releaser').order_by('nick__name', 'category'),
		'featured_in_productions': [
			appearance.production for appearance in
			production.appearances_as_soundtrack.select_related('production', 'production__default_screenshot').order_by('production__release_date_date')
		],
		'competition_placings': production.competition_placings.order_by('competition__party__start_date_date'),
		'invitation_parties': production.invitation_parties.order_by('start_date_date'),
		'tags': production.tags.all(),
		'blurbs': production.blurbs.all() if request.user.is_staff else None,
		'comment_form': comment_form,
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
			download_link_formset.save()
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
