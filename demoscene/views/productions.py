from demoscene.shortcuts import *
from demoscene.models import Production, Nick, Credit, DownloadLink, Screenshot
from demoscene.forms import CreateProductionForm, ProductionTypeFormSet, ProductionPlatformFormSet, DownloadLinkFormSet, AttachedNickFormSet, ProductionAddCreditForm, ProductionEditNotesForm, ProductionDownloadLinkForm, ProductionEditCoreDetailsForm, ProductionEditExternalLinksForm, ProductionAddScreenshotFormset

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	production_page = get_page(
		Production.objects.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'productions/index.html', {
		'production_page': production_page,
	})

def show(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name'),
	})

@login_required
def edit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/show.html', {
		'production': production,
		'author_nicks': production.author_nicks.all(),
		'author_affiliation_nicks': production.author_affiliation_nicks.all(),
		'credits': production.credits.order_by('nick__name'),
		'editing': True,
		'editing_as_admin': request.user.is_staff,
	})
	
@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionEditCoreDetailsForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		author_formset = AttachedNickFormSet(request.POST, prefix = 'authors')
		affiliation_formset = AttachedNickFormSet(request.POST, prefix = 'affiliations')
		
		if (
			form.is_valid() and production_type_formset.is_valid()
			and production_platform_formset.is_valid()
			and author_formset.is_valid() and affiliation_formset.is_valid()
			):
			form.save()
			production.types = get_production_types(production_type_formset)
			production.platforms = get_production_platforms(production_platform_formset)
			production.author_nicks = [form.matched_nick() for form in author_formset.forms]
			production.author_affiliation_nicks = [form.matched_nick() for form in affiliation_formset.forms]
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionEditCoreDetailsForm(instance = production)
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type',
			initial = [{'production_type': typ.id} for typ in production.types.all()])
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform',
			initial = [{'platform': platform.id} for platform in production.platforms.all()])
		author_formset = AttachedNickFormSet(prefix = 'authors',
			initial = [{'nick_id': nick.id, 'name': nick.name} for nick in production.author_nicks.all()])
		affiliation_formset = AttachedNickFormSet(prefix = 'affiliations',
			initial = [{'nick_id': nick.id, 'name': nick.name} for nick in production.author_affiliation_nicks.all()])
	
	return ajaxable_render(request, 'productions/edit_core_details.html', {
		'production': production,
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'author_formset': author_formset,
		'affiliation_formset': affiliation_formset,
	})

@login_required
def edit_notes(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
		title = 'Editing notes for %s:' % production.title)

@login_required
def edit_external_links(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_external_links', production, ProductionEditExternalLinksForm,
		title = 'Editing external links for %s:' % production.title)

@login_required
def add_download_link(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = DownloadLink(production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Adding download link for %s:" % production.title,
		'action_url': reverse('production_add_download_link', args=[production.id]),
	})

@login_required
def edit_download_link(request, production_id, download_link_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = get_object_or_404(DownloadLink, id = download_link_id, production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'productions/edit_download_link.html', {
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
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_download_link', args = [production_id, download_link_id]),
			"Are you sure you want to delete this download link for %s?" % production.title )

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
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionAddScreenshotFormset()
	return ajaxable_render(request, 'productions/add_screenshot.html', {
		'production': production,
		'formset': formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		production = Production()
		form = CreateProductionForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		author_formset = AttachedNickFormSet(request.POST, prefix = 'authors')
		affiliation_formset = AttachedNickFormSet(request.POST, prefix = 'affiliations')
		if (
			form.is_valid() and production_type_formset.is_valid()
			and production_platform_formset.is_valid() and download_link_formset.is_valid()
			and author_formset.is_valid() and affiliation_formset.is_valid()
			):
			form.save()
			download_link_formset.save()
			production.types = get_production_types(production_type_formset)
			production.platforms = get_production_platforms(production_platform_formset)
			production.author_nicks = [form.matched_nick() for form in author_formset.forms]
			production.author_affiliation_nicks = [form.matched_nick() for form in affiliation_formset.forms]
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet()
		author_formset = AttachedNickFormSet(prefix = 'authors')
		affiliation_formset = AttachedNickFormSet(prefix = 'affiliations')
	return ajaxable_render(request, 'productions/create.html', {
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'download_link_formset': download_link_formset,
		'author_formset': author_formset,
		'affiliation_formset': affiliation_formset,
	})

@login_required
def add_credit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionAddCreditForm(request.POST)
		if form.is_valid():
			nick = Nick.from_id_and_name(form.cleaned_data['nick_id'], form.cleaned_data['nick_name'])
			credit = Credit(
				production = production,
				nick = nick,
				role = form.cleaned_data['role']
			)
			credit.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionAddCreditForm()
	return ajaxable_render(request, 'productions/add_credit.html', {
		'production': production,
		'form': form,
	})

@login_required
def edit_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		form = ProductionAddCreditForm(request.POST)
		if form.is_valid():
			nick = Nick.from_id_and_name(form.cleaned_data['nick_id'], form.cleaned_data['nick_name'])
			credit.nick = nick
			credit.role = form.cleaned_data['role']
			credit.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionAddCreditForm({
			'nick_name': credit.nick.name,
			'nick_id': credit.nick_id,
			'role': credit.role
		})
	return ajaxable_render(request, 'productions/edit_credit.html', {
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
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_credit', args = [production_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, production.title) )

def autocomplete(request):
	query = request.GET.get('q')
	productions = Production.objects.filter(title__istartswith = query)[:10]
	return render(request, 'productions/autocomplete.txt', {
		'query': query,
		'productions': productions,
	}, mimetype = 'text/plain')

# helper functions
def get_production_types(production_type_formset):
	prod_types = []
	for prod_type_form in production_type_formset.forms:
		if hasattr(prod_type_form, 'cleaned_data') and prod_type_form.cleaned_data.get('production_type'):
			prod_types.append(prod_type_form.cleaned_data['production_type'])
	for prod_type_form in production_type_formset.deleted_forms:
		if hasattr(prod_type_form, 'cleaned_data') and prod_type_form.cleaned_data.get('production_type') and prod_type_form.cleaned_data['production_type'] in prod_types:
			prod_types.remove(prod_type_form.cleaned_data['production_type'])
	return prod_types

def get_production_platforms(production_platform_formset):
	platforms = []
	for prod_platform_form in production_platform_formset.forms:
		if hasattr(prod_platform_form, 'cleaned_data') and prod_platform_form.cleaned_data.get('platform'):
			platforms.append(prod_platform_form.cleaned_data['platform'])
	for prod_platform_form in production_platform_formset.deleted_forms:
		if hasattr(prod_platform_form, 'cleaned_data') and prod_platform_form.cleaned_data.get('platform') and prod_platform_form.cleaned_data['platform'] in platforms:
			platforms.remove(prod_platform_form.cleaned_data['platform'])
	return platforms
