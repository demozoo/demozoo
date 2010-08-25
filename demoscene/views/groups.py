from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, NickVariant
from demoscene.forms import GroupAddMemberForm, CreateGroupForm

from django.contrib.auth.decorators import login_required

def index(request):
	nick_page = get_page(
		Nick.objects.filter(releaser__is_group = True).extra(
			select={'lower_name': 'lower(demoscene_nick.name)'}
		).order_by('lower_name'),
		request.GET.get('page', '1') )
	
	return render(request, 'groups/index.html', {
		'nick_page': nick_page,
	})

def show(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	return render(request, 'groups/show.html', {
		'group': group,
		'members': group.members.order_by('name'),
	})

@login_required
def edit(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	return render(request, 'groups/show.html', {
		'group': group,
		'editing': True,
		'editing_as_admin': request.user.is_staff,
	})

@login_required
def create(request):
	if request.method == 'POST':
		group = Releaser(is_group = True)
		form = CreateGroupForm(request.POST, instance = group)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = CreateGroupForm()
	
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "New group",
		'action_url': reverse('new_group'),
	})

@login_required
def add_member(request, group_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		form = GroupAddMemberForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['scener_id'] == 'newscener':
				scener = Releaser(name = form.cleaned_data['scener_name'], is_group = False)
				scener.save()
			else:
				# TODO: test for blank scener_id (as sent by non-JS)
				scener = Releaser.objects.get(id = form.cleaned_data['scener_id'], is_group = False)
			group.members.add(scener)
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = GroupAddMemberForm()
	return ajaxable_render(request, 'groups/add_member.html', {
		'group': group,
		'form': form,
	})

@login_required
def remove_member(request, group_id, scener_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			group.members.remove(scener)
		return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('group_remove_member', args = [group_id, scener_id]),
			"Are you sure you want to remove %s from the group %s?" % (scener.name, group.name) )

def autocomplete(request):
	query = request.GET.get('q')
	new_option = request.GET.get('new_option', False)
	nick_variants = NickVariant.autocompletion_search(query,
		limit = request.GET.get('limit', 10),
		exact = request.GET.get('exact', False),
		groups_only = True,
		members = request.GET.getlist('member[]')
	)
	return render(request, 'groups/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')
	