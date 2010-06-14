from demoscene.shortcuts import *
from demoscene.models import Releaser
from demoscene.forms import GroupForm, GroupAddMemberForm

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	groups = Releaser.objects.filter(is_group = True).order_by('name')
	return render(request, 'groups/index.html', {
		'groups': groups,
	})

def show(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	return render(request, 'groups/show.html', {
		'group': group,
	})

@login_required
def edit(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		form = GroupForm(request.POST, instance = group)
		if form.is_valid():
			form.save()
			messages.success(request, 'Group updated')
			return redirect('group', args = [group.id])
	else:
		form = GroupForm(instance = group)
	
	return render(request, 'groups/edit.html', {
		'group': group,
		'form': form,
	})

@login_required
def create(request):
	if request.method == 'POST':
		group = Releaser(is_group = True)
		form = GroupForm(request.POST, instance = group)
		if form.is_valid():
			form.save()
			messages.success(request, 'Group added')
			return redirect('group', args = [group.id])
	else:
		form = GroupForm()
	return render(request, 'groups/create.html', {
		'form': form,
	})

@login_required
def add_member(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		form = GroupAddMemberForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['scener_id'] == 'new':
				scener = Releaser(name = form.cleaned_data['scener_name'], is_group = False)
				scener.save()
			else:
				# TODO: test for blank scener_id (as sent by non-JS)
				scener = Releaser.objects.get(id = form.cleaned_data['scener_id'], is_group = False)
			group.members.add(scener)
			return redirect('group', args = [group.id])
	else:
		form = GroupAddMemberForm()
	return render(request, 'groups/add_member.html', {
		'group': group,
		'form': form,
	})

def autocomplete(request):
	query = request.GET.get('q')
	limit = request.GET.get('limit', 10)
	new_option = request.GET.get('new_option', False)
	if query:
		# TODO: search on nick variants, not just group names
		groups = Releaser.objects.filter(
			is_group = True, name__istartswith = query)[:limit]
	else:
		groups = Releaser.objects.none()
	return render(request, 'groups/autocomplete.txt', {
		'query': query,
		'groups': groups,
		'new_option': new_option,
	}, mimetype = 'text/plain')
	