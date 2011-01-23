from demoscene.shortcuts import *
from demoscene.models import Production, ProductionType, Byline
from demoscene.forms.production import *

from django.contrib.auth.decorators import login_required
import datetime

def index(request):
	queryset = Production.objects.filter(types__in = ProductionType.graphic_types())
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'graphics/index.html', {
		'production_page': production_page,
	})

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'graphics':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'graphics/show.html', {
		'production': production,
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.ordered_download_links(),
		'competition_placings': production.competition_placings.order_by('competition__party__start_date'),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})

@login_required
def edit(request, production_id):
	set_edit_mode_active(True, request.user)
	return show(request, production_id, edit_mode = True)

@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = GraphicsEditCoreDetailsForm(request.POST, instance = production)
		
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = GraphicsEditCoreDetailsForm(instance = production)
	
	return ajaxable_render(request, 'graphics/edit_core_details.html', {
		'production': production,
		'form': form,
	})

@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at = datetime.datetime.now())
		form = CreateGraphicsForm(request.POST, instance = production)
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateGraphicsForm(initial = {
			'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
		})
		download_link_formset = DownloadLinkFormSet()
	return ajaxable_render(request, 'graphics/create.html', {
		'form': form,
		'download_link_formset': download_link_formset,
	})
