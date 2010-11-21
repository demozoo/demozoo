from demoscene.shortcuts import *
from demoscene.models import Production, ProductionType
from demoscene.forms.production import *

from django.contrib.auth.decorators import login_required
import datetime

def index(request):
	queryset = Production.objects.filter(types__in = ProductionType.music_types())
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'music/index.html', {
		'production_page': production_page,
	})
	return index_common(request, 'Music',
	)

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'music':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'music/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name'),
		'download_links': production.ordered_download_links(),
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
		form = MusicEditCoreDetailsForm(request.POST, instance = production)
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		
		if form.is_valid() and production_platform_formset.is_valid():
			production.updated_at = datetime.datetime.now()
			form.save()
			production.platforms = production_platform_formset.get_production_platforms()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = MusicEditCoreDetailsForm(instance = production)
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform',
			initial = [{'platform': platform.id} for platform in production.platforms.all()])
	
	return ajaxable_render(request, 'music/edit_core_details.html', {
		'production': production,
		'form': form,
		'production_platform_formset': production_platform_formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at = datetime.datetime.now())
		form = CreateMusicForm(request.POST, instance = production)
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateMusicForm()
		download_link_formset = DownloadLinkFormSet()
	return ajaxable_render(request, 'music/create.html', {
		'form': form,
		'download_link_formset': download_link_formset,
	})
