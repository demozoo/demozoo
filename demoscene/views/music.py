from demoscene.shortcuts import *
from demoscene.models import Production, ProductionType, Byline
from demoscene.forms.production import *
from taggit.models import Tag

from django.contrib.auth.decorators import login_required
import datetime

def index(request):
	queryset = Production.objects.filter(supertype = 'music')
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'music/index.html', {
		'title': 'Music',
		'add_new_link': True,
		'production_page': production_page,
	})

def tagged(request, tag_slug):
	try:
		tag = Tag.objects.get(slug = tag_slug)
	except Tag.DoesNotExist:
		tag = Tag(name = tag_slug)
	queryset = Production.objects.filter(supertype = 'music', tags__slug = tag_slug)
	
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'music/index.html', {
		'title': "Music tagged '%s'" % tag.name,
		'add_new_link': False,
		'production_page': production_page,
	})

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'music':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'music/show.html', {
		'production': production,
		'download_links': production.ordered_download_links(),
		'featured_in_productions': [
			appearance.production for appearance in
			production.appearances_as_soundtrack.select_related('production').order_by('production__release_date_date')
		],
		'competition_placings': production.competition_placings.order_by('competition__party__start_date'),
		'tags': production.tags.all(),
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
		
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = MusicEditCoreDetailsForm(instance = production)
	
	return ajaxable_render(request, 'music/edit_core_details.html', {
		'html_title': "Editing music: %s" % production.title,
		'production': production,
		'form': form,
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
		form = CreateMusicForm(initial = {
			'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
		})
		download_link_formset = DownloadLinkFormSet()
	return ajaxable_render(request, 'music/create.html', {
		'html_title': "New music",
		'form': form,
		'download_link_formset': download_link_formset,
	})
