from demoscene.shortcuts import *
from demoscene.models import Production, Byline, Releaser, Credit, DownloadLink, Screenshot, ProductionType
from demoscene.forms.production import *

from django.contrib.auth.decorators import login_required
import datetime

def productions_index(request):
	queryset = Production.objects.exclude(types__in = ProductionType.music_types()).\
		exclude(types__in = ProductionType.graphic_types())
	
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'productions/index.html', {
		'title': "Productions",
		'add_new_link': True,
		'production_page': production_page,
	})

def tagged(request, tag_name):
	queryset = Production.objects.filter(tags__name = tag_name).\
		exclude(types__in = ProductionType.music_types()).\
		exclude(types__in = ProductionType.graphic_types())
	
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'productions/index.html', {
		'title': "Productions tagged '%s'" % tag_name,
		'add_new_link': False,
		'production_page': production_page,
	})

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'production':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name'),
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.ordered_download_links(),
		'soundtracks': [
			link.soundtrack for link in
			production.soundtrack_links.order_by('position').select_related('soundtrack')
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

def edit_done(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(production.get_absolute_url())
	
@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionEditCoreDetailsForm(request.POST, instance = production)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionEditCoreDetailsForm(instance = production)
	
	return ajaxable_render(request, 'productions/edit_core_details.html', {
		'html_title': "Editing production: %s" % production.title,
		'production': production,
		'form': form,
	})

@login_required
def edit_notes(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
		title = 'Editing notes for %s:' % production.title,
		update_datestamp = True, update_bonafide_flag = True)

@login_required
def edit_external_links(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_external_links', production, ProductionEditExternalLinksForm,
		title = 'Editing external links for %s:' % production.title,
		update_datestamp = True, update_bonafide_flag = True)

@login_required
def add_download_link(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = DownloadLink(production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Adding download link for %s:" % production.title,
		'html_title': "Adding download link for %s" % production.title,
		'action_url': reverse('production_add_download_link', args=[production.id]),
	})

@login_required
def edit_download_link(request, production_id, download_link_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = get_object_or_404(DownloadLink, id = download_link_id, production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'productions/edit_download_link.html', {
		'html_title': "Editing download link for %s" % production.title,
		'form': form,
		'production': production,
		'download_link': download_link,
	})

@login_required
def delete_download_link(request, production_id, download_link_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = get_object_or_404(DownloadLink, id = download_link_id, production = production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			download_link.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_download_link', args = [production_id, download_link_id]),
			"Are you sure you want to delete this download link for %s?" % production.title,
			html_title = "Deleting download link for %s" % production.title )

@login_required
def screenshots(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/screenshots.html', {
		'production': production,
		'screenshots': production.screenshots.order_by('id'),
	})

@login_required
def add_screenshot(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		formset = ProductionAddScreenshotFormset(request.POST, request.FILES)
		if formset.is_valid():
			for form in formset.forms:
				screenshot = form.save(commit = False)
				if screenshot.original:
					screenshot.production = production
					screenshot.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionAddScreenshotFormset()
	return ajaxable_render(request, 'productions/add_screenshot.html', {
		'html_title': "Adding screenshots for %s" % production.title,
		'production': production,
		'formset': formset,
	})

@login_required
def delete_screenshot(request, production_id, screenshot_id):
	production = get_object_or_404(Production, id = production_id)
	screenshot = get_object_or_404(Screenshot, id = screenshot_id, production = production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			screenshot.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(reverse('production_screenshots', args=[production.id]))
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_screenshot', args = [production_id, screenshot_id]),
			"Are you sure you want to delete this screenshot for %s?" % production.title,
			html_title = "Deleting screenshot for %s" % production.title )

@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at = datetime.datetime.now())
		form = CreateProductionForm(request.POST, instance = production)
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateProductionForm(initial = {
			'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
		})
		download_link_formset = DownloadLinkFormSet()
	return ajaxable_render(request, 'productions/create.html', {
		'html_title': "New production",
		'form': form,
		'download_link_formset': download_link_formset,
	})

@login_required
def add_credit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	credit = Credit(production = production)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/add_credit.html', {
		'html_title': "Adding credit for %s" % production.title,
		'production': production,
		'form': form,
	})

@login_required
def edit_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/edit_credit.html', {
		'html_title': "Editing credit for %s" % production.title,
		'production': production,
		'credit': credit,
		'form': form,
	})

@login_required
def delete_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			credit.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_credit', args = [production_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, production.title),
			html_title = "Deleting %s's credit from %s" % (credit.nick.name, production.title) )

@login_required
def edit_soundtracks(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		formset = ProductionSoundtrackLinkFormset(request.POST, instance = production)
		if formset.is_valid():
			def form_order_key(form):
				if form.is_valid():
					return form.cleaned_data['ORDER'] or 9999
				else:
					return 9999
			
			sorted_forms = sorted(formset.forms, key = form_order_key)
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i+1
			formset.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			for stl in production.soundtrack_links.all():
				stl.soundtrack.has_bonafide_edits = True
				stl.soundtrack.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionSoundtrackLinkFormset(instance = production)
	return ajaxable_render(request, 'productions/edit_soundtracks.html', {
		'html_title': "Editing soundtrack details for %s" % production.title,
		'production': production,
		'formset': formset,
	})

@login_required
def add_tag(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		if request.POST.get('tag_name', '').strip():
			production.tags.add(request.POST.get('tag_name').strip())
	return HttpResponseRedirect(production.get_absolute_edit_url())

@login_required
def remove_tag(request, production_id, tag_name):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		production.tags.remove(tag_name)
	return HttpResponseRedirect(production.get_absolute_edit_url())

def autocomplete(request):
	query = request.GET.get('q')
	productions = Production.objects.filter(title__istartswith = query)
	supertype = request.GET.get('supertype')
	if supertype:
		productions = productions.filter(supertype = supertype)
	productions = productions[:10]
	return render(request, 'productions/autocomplete.txt', {
		'query': query,
		'productions': productions,
	}, mimetype = 'text/plain')
