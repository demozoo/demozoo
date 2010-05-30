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
		if form.is_valid():
			form.save()
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm(instance = production)
	
	return render(request, 'productions/edit.html', {
		'production': production,
		'form': form,
	})

def create(request):
	if request.method == 'POST':
		form = ProductionForm(request.POST)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		if form.is_valid() and production_type_formset.is_valid():
			production = form.save()
			for prod_type_form in production_type_formset.forms:
				production.types.add(prod_type_form.cleaned_data['production_type'])
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
	return render(request, 'productions/create.html', {
		'form': form,
		'production_type_formset': production_type_formset,
	})
