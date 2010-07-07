from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, NickVariant
from demoscene.forms import GroupForm, GroupAddMemberForm, NickForm, NickFormSet

from django.contrib import messages
from django.contrib.auth.decorators import login_required

def index(request):
	nicks = Nick.objects.filter(releaser__is_group = True).order_by('name')
	return render(request, 'groups/index.html', {
		'nicks': nicks,
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
		primary_nick = group.primary_nick
		primary_nick_form = NickForm(request.POST, prefix = 'primary_nick', instance = primary_nick)
		alternative_nicks_formset = NickFormSet(request.POST, prefix = 'alternative_nicks', queryset = group.alternative_nicks)
		if primary_nick_form.is_valid() and alternative_nicks_formset.is_valid():
			primary_nick_form.save() # may indirectly update name of Releaser and save it too
			alternative_nicks = alternative_nicks_formset.save(commit = False)
			for nick in alternative_nicks:
				nick.releaser = group
				nick.save()
			messages.success(request, 'Group updated')
			return redirect('group', args = [group.id])
	else:
		primary_nick_form = NickForm(prefix = 'primary_nick', instance = group.primary_nick)
		alternative_nicks_formset = NickFormSet(prefix = 'alternative_nicks', queryset = group.alternative_nicks)
	
	return render(request, 'groups/edit.html', {
		'group': group,
		'primary_nick_form': primary_nick_form,
		'alternative_nicks_formset': alternative_nicks_formset,
	})

@login_required
def create(request):
	if request.method == 'POST':
		group = Releaser(is_group = True)
		primary_nick_form = NickForm(request.POST, prefix = 'primary_nick')
		alternative_nicks_formset = NickFormSet(request.POST, prefix = 'alternative_nicks', queryset = group.alternative_nicks)
		if primary_nick_form.is_valid() and alternative_nicks_formset.is_valid():
			group.name = primary_nick_form.cleaned_data['name']
			group.save() # this will cause a primary nick record to be created; update it with form details
			primary_nick_form = NickForm(request.POST, prefix = 'primary_nick', instance = group.primary_nick)
			primary_nick_form.save()
			alternative_nicks = alternative_nicks_formset.save(commit = False)
			for nick in alternative_nicks:
				nick.releaser = group
				nick.save()
			
			messages.success(request, 'Group added')
			return redirect('group', args = [group.id])
	else:
		primary_nick_form = NickForm(prefix = 'primary_nick')
		alternative_nicks_formset = NickFormSet(prefix = 'alternative_nicks', queryset = Nick.objects.none())
	return render(request, 'groups/create.html', {
		'primary_nick_form': primary_nick_form,
		'alternative_nicks_formset': alternative_nicks_formset,
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

@login_required
def remove_member(request, group_id, scener_id):
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			group.members.remove(scener)
		return redirect('group', args = [group.id])
	else:
		return render(request, 'groups/remove_member.html', {
			'group': group,
			'scener': scener,
		})

def autocomplete(request):
	query = request.GET.get('q')
	limit = request.GET.get('limit', 10)
	members = [name.lower() for name in request.GET.getlist('member')]
	new_option = request.GET.get('new_option', False)
	if query:
		nick_variants = NickVariant.objects.filter(
			nick__releaser__is_group = True,
			name__istartswith = query)
		if members:
			nick_variants = nick_variants.extra(
				select = {
					'score': '''
						SELECT COUNT(*) FROM demoscene_releaser_groups
						INNER JOIN demoscene_releaser AS member ON (demoscene_releaser_groups.from_releaser_id = member.id)
						INNER JOIN demoscene_nick AS member_nick ON (member.id = member_nick.releaser_id)
						INNER JOIN demoscene_nickvariant AS member_nickvariant ON (member_nick.id = member_nickvariant.nick_id)
						WHERE demoscene_releaser_groups.to_releaser_id = demoscene_releaser.id
						AND LOWER(member_nickvariant.name) IN (%s)
					'''
				},
				select_params = (tuple(members), ),
				order_by = ('-score','name')
			)
		else:
			nick_variants = nick_variants.extra(
				select = {'score': '0'},
				order_by = ('name',)
			)
		nick_variants = nick_variants[:limit]
	else:
		nick_variants = NickVariant.objects.none()
	return render(request, 'groups/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')
	