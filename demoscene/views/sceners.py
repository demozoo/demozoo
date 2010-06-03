from demoscene.shortcuts import *
from demoscene.models import Releaser
from demoscene.forms import ScenerForm

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
