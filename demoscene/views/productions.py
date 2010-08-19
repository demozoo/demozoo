from demoscene.shortcuts import *
from demoscene.models import Production, Nick, Credit
from demoscene.forms import ProductionForm, AdminProductionForm, ProductionTypeFormSet, ProductionPlatformFormSet, DownloadLinkFormSet, AttachedNickFormSet, ProductionAddCreditForm

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
		'author_nicks': production.author_nicks.all(),
		'author_affiliation_nicks': production.author_affiliation_nicks.all(),
		'credits': production.credits.order_by('nick__name'),
	})

@login_required
def edit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		if request.user.is_staff:
			form = AdminProductionForm(request.POST, instance = production)
		else:
			form = ProductionForm(request.POST, instance = production)
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
			messages.success(request, 'Production updated')
			return redirect('production', args = [production.id])
	else:
		if request.user.is_staff:
			form = AdminProductionForm(instance = production)
		else:
			form = ProductionForm(instance = production)
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type',
			initial = [{'production_type': typ.id} for typ in production.types.all()])
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform',
			initial = [{'platform': platform.id} for platform in production.platforms.all()])
		download_link_formset = DownloadLinkFormSet(instance = production)
		author_formset = AttachedNickFormSet(prefix = 'authors',
			initial = [{'nick_id': nick.id, 'name': nick.name} for nick in production.author_nicks.all()])
		affiliation_formset = AttachedNickFormSet(prefix = 'affiliations',
			initial = [{'nick_id': nick.id, 'name': nick.name} for nick in production.author_affiliation_nicks.all()])
	
	return render(request, 'productions/edit.html', {
		'production': production,
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'download_link_formset': download_link_formset,
		'author_formset': author_formset,
		'affiliation_formset': affiliation_formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		production = Production()
		if request.user.is_staff:
			form = AdminProductionForm(request.POST, instance = production)
		else:
			form = ProductionForm(request.POST, instance = production)
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
			messages.success(request, 'Production added')
			return redirect('production', args = [production.id])
	else:
		if request.user.is_staff:
			form = AdminProductionForm()
		else:
			form = ProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet()
		author_formset = AttachedNickFormSet(prefix = 'authors')
		affiliation_formset = AttachedNickFormSet(prefix = 'affiliations')
	return render(request, 'productions/create.html', {
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
			return redirect('production', args = [production.id])
	else:
		form = ProductionAddCreditForm()
	return render(request, 'productions/add_credit.html', {
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
			return redirect('production', args = [production.id])
	else:
		form = ProductionAddCreditForm({
			'nick_name': credit.nick.name,
			'nick_id': credit.nick_id,
			'role': credit.role
		})
	return render(request, 'productions/edit_credit.html', {
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
		return redirect('production', args = [production.id])
	else:
		return render(request, 'productions/delete_credit.html', {
			'production': production,
			'credit': credit,
		})

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
