from demoscene.shortcuts import *
from demoscene.models import Production
from demoscene.forms import ProductionForm, ProductionTypeFormSet

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

def edit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		if form.is_valid() and production_type_formset.is_valid():
			form.save()
			production.types = get_production_types(production_type_formset)
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm(instance = production)
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type',
			initial = [{'production_type': typ.id} for typ in production.types.all()])
	
	return render(request, 'productions/edit.html', {
		'production': production,
		'form': form,
		'production_type_formset': production_type_formset,
	})

def create(request):
	if request.method == 'POST':
		form = ProductionForm(request.POST)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		if form.is_valid() and production_type_formset.is_valid():
			production = form.save()
			production.types = get_production_types(production_type_formset)
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
	return render(request, 'productions/create.html', {
		'form': form,
		'production_type_formset': production_type_formset,
	})

# helper functions
def get_production_types(production_type_formset):
	prod_types = []
	for prod_type_form in production_type_formset.forms:
		if prod_type_form.cleaned_data.get('production_type'):
			prod_types.append(prod_type_form.cleaned_data['production_type'])
	for prod_type_form in production_type_formset.deleted_forms:
		if prod_type_form.cleaned_data.get('production_type') and prod_type_form.cleaned_data['production_type'] in prod_types:
			prod_types.remove(prod_type_form.cleaned_data['production_type'])
	return prod_types
