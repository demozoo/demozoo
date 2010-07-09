from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, NickVariant
from demoscene.forms import ScenerForm, ScenerAddGroupForm, NickForm, NickFormSet

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	nicks = Nick.objects.filter(releaser__is_group = False).order_by('name')
	return render(request, 'sceners/index.html', {
		'nicks': nicks,
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
		primary_nick = scener.primary_nick
		primary_nick_form = NickForm(request.POST, prefix = 'primary_nick', instance = primary_nick)
		alternative_nicks_formset = NickFormSet(request.POST, prefix = 'alternative_nicks', queryset = scener.alternative_nicks)
		if primary_nick_form.is_valid() and alternative_nicks_formset.is_valid():
			primary_nick_form.save() # may indirectly update name of Releaser and save it too
			alternative_nicks = alternative_nicks_formset.save(commit = False)
			for nick in alternative_nicks:
				nick.releaser = scener
				nick.save()
			messages.success(request, 'Scener updated')
			return redirect('scener', args = [scener.id])
	else:
		primary_nick_form = NickForm(prefix = 'primary_nick', instance = scener.primary_nick)
		alternative_nicks_formset = NickFormSet(prefix = 'alternative_nicks', queryset = scener.alternative_nicks)
	
	return render(request, 'sceners/edit.html', {
		'scener': scener,
		'primary_nick_form': primary_nick_form,
		'alternative_nicks_formset': alternative_nicks_formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		scener = Releaser(is_group = False)
		primary_nick_form = NickForm(request.POST, prefix = 'primary_nick')
		alternative_nicks_formset = NickFormSet(request.POST, prefix = 'alternative_nicks', queryset = scener.alternative_nicks)
		if primary_nick_form.is_valid() and alternative_nicks_formset.is_valid():
			scener.name = primary_nick_form.cleaned_data['name']
			scener.save() # this will cause a primary nick record to be created; update it with form details
			primary_nick_form = NickForm(request.POST, prefix = 'primary_nick', instance = scener.primary_nick)
			primary_nick_form.save()
			alternative_nicks = alternative_nicks_formset.save(commit = False)
			for nick in alternative_nicks:
				nick.releaser = scener
				nick.save()
			
			messages.success(request, 'Scener added')
			return redirect('scener', args = [scener.id])
	else:
		primary_nick_form = NickForm(prefix = 'primary_nick')
		alternative_nicks_formset = NickFormSet(prefix = 'alternative_nicks', queryset = Nick.objects.none())
	return render(request, 'sceners/create.html', {
		'primary_nick_form': primary_nick_form,
		'alternative_nicks_formset': alternative_nicks_formset,
	})

@login_required
def add_group(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		form = ScenerAddGroupForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['group_id'] == 'newgroup':
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

@login_required
def remove_group(request, scener_id, group_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			scener.groups.remove(group)
		return redirect('scener', args = [scener.id])
	else:
		return render(request, 'sceners/remove_group.html', {
			'scener': scener,
			'group': group,
		})

def autocomplete(request):
	query = request.GET.get('q')
	new_option = request.GET.get('new_option', False)
	
	nick_variants = NickVariant.autocompletion_search(query,
		limit = request.GET.get('limit', 10),
		exact = request.GET.get('exact', False),
		sceners_only = True,
		groups = request.GET.getlist('group[]')
	)
	return render(request, 'sceners/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')
