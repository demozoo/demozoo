from demoscene.shortcuts import *
from demoscene.models import Releaser
from demoscene.forms import ScenerForm, ScenerAddGroupForm

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	sceners = Releaser.objects.filter(is_group = False).order_by('name')
	return render(request, 'sceners/index.html', {
		'sceners': sceners,
	})

def show(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	return render(request, 'sceners/show.html', {
		'scener': scener,
	})

@login_required
def edit(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		form = ScenerForm(request.POST, instance = scener)
		if form.is_valid():
			form.save()
			messages.success(request, 'Scener updated')
			return redirect('scener', args = [scener.id])
	else:
		form = ScenerForm(instance = scener)
	
	return render(request, 'sceners/edit.html', {
		'scener': scener,
		'form': form,
	})

@login_required
def create(request):
	if request.method == 'POST':
		scener = Releaser(is_group = False)
		form = ScenerForm(request.POST, instance = scener)
		if form.is_valid():
			form.save()
			messages.success(request, 'Scener added')
			return redirect('scener', args = [scener.id])
	else:
		form = ScenerForm()
	return render(request, 'sceners/create.html', {
		'form': form,
	})

@login_required
def add_group(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		form = ScenerAddGroupForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['group_id'] == 'new':
				group = Releaser(name = form.cleaned_data['group_name'], is_group = True)
				group.save()
			else:
				# TODO: test for blank group_id (as sent by non-JS)
				group = Releaser.objects.get(id = form.cleaned_data['group_id'], is_group = True)
			scener.groups.add(group)
			return redirect('scener', args = [scener.id])
	else:
		form = ScenerAddGroupForm()
	return render(request, 'sceners/add_group.html', {
		'scener': scener,
		'form': form,
	})

def autocomplete(request):
	query = request.GET.get('q')
	limit = request.GET.get('limit', 10)
	new_option = request.GET.get('new_option', False)
	if query:
		# TODO: search on nick variants, not just releaser names
		sceners = Releaser.objects.filter(
			is_group = False, name__istartswith = query)[:limit]
	else:
		sceners = Releaser.objects.none()
	return render(request, 'sceners/autocomplete.txt', {
		'query': query,
		'sceners': sceners,
		'new_option': new_option,
	}, mimetype = 'text/plain')
