from demoscene.shortcuts import *
from demoscene.models import Production
from demoscene.forms import ProductionForm, ProductionTypeFormSet, ProductionPlatformFormSet, DownloadLinkFormSet

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	productions = Production.objects.order_by('title')
	return render(request, 'productions/index.html', {
		'productions': productions,
	})

def show(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/show.html', {
		'production': production,
	})

@login_required
def edit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and production_type_formset.is_valid() and production_platform_formset.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			production.types = get_production_types(production_type_formset)
			production.platforms = get_production_platforms(production_platform_formset)
			messages.success(request, 'Production updated')
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm(instance = production)
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type',
			initial = [{'production_type': typ.id} for typ in production.types.all()])
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform',
			initial = [{'platform': platform.id} for platform in production.platforms.all()])
		download_link_formset = DownloadLinkFormSet(instance = production)
	
	return render(request, 'productions/edit.html', {
		'production': production,
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'download_link_formset': download_link_formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		production = Production()
		form = ProductionForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and production_type_formset.is_valid() and production_platform_formset.is_valid():
			form.save()
			download_link_formset.save()
			production.types = get_production_types(production_type_formset)
			production.platforms = get_production_platforms(production_platform_formset)
			messages.success(request, 'Production added')
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet()
	return render(request, 'productions/create.html', {
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'download_link_formset': download_link_formset,
	})

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
