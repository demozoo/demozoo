from demoscene.shortcuts import *
from demoscene.models import Production
from demoscene.forms import ProductionForm

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
		if form.is_valid():
			production = form.save()
			return redirect('production', args = [production.id])
	else:
		form = ProductionForm()
	return render(request, 'productions/create.html', {
		'form': form,
	})
