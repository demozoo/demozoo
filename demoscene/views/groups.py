from demoscene.shortcuts import *
from demoscene.models import Releaser
from demoscene.forms import GroupForm

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

def edit(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		form = GroupForm(request.POST, instance = group)
		if form.is_valid():
			form.save()
			return redirect('group', args = [group.id])
	else:
		form = GroupForm(instance = group)
	
	return render(request, 'groups/edit.html', {
		'group': group,
		'form': form,
	})

def create(request):
	if request.method == 'POST':
		group = Releaser(is_group = True)
		form = GroupForm(request.POST, instance = group)
		if form.is_valid():
			form.save()
			return redirect('group', args = [group.id])
	else:
		form = GroupForm()
	return render(request, 'groups/create.html', {
		'form': form,
	})
