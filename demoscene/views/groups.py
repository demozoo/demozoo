from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, Membership, Edit
from demoscene.forms.releaser import *

from django.contrib.auth.decorators import login_required
import datetime


def index(request):
	nick_page = get_page(
		Nick.objects.filter(releaser__is_group=True).extra(
			select={'lower_name': 'lower(demoscene_nick.name)'}
		).order_by('lower_name'),
		request.GET.get('page', '1'))

	return render(request, 'groups/index.html', {
		'nick_page': nick_page,
	})


def show(request, group_id, edit_mode=False):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)

	edit_mode = edit_mode or sticky_editing_active(request.user)

	return render(request, 'groups/show.html', {
		'group': group,
		'supergroupships': group.group_memberships.all().select_related('group').order_by('-is_current', 'group__name'),
		'memberships': group.member_memberships.filter(member__is_group=False).select_related('member').order_by('-is_current', 'member__name'),
		'subgroupships': group.member_memberships.filter(member__is_group=True).select_related('member').order_by('-is_current', 'member__name'),
		'productions': group.productions().order_by('-release_date_date', '-title'),
		'member_productions': group.member_productions().order_by('-release_date_date', '-title'),
		'credits': group.credits().order_by('-production__release_date_date', '-production__title'),
		'external_links': group.external_links.all(),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})


@login_required
def edit(request, group_id):
	set_edit_mode_active(True, request.user)
	return show(request, group_id, edit_mode=True)


def edit_done(request, group_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(group.get_absolute_url())


def history(request, group_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	return render(request, 'groups/history.html', {
		'group': group,
		'edits': Edit.for_model(group),
	})


@login_required
def create(request):
	if request.method == 'POST':
		group = Releaser(is_group=True, updated_at=datetime.datetime.now())
		form = CreateGroupForm(request.POST, instance=group)
		if form.is_valid():
			form.save()
			form.log_creation(request.user)
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = CreateGroupForm()

	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "New group",
		'html_title': "New group",
		'action_url': reverse('new_group'),
	})


@login_required
def add_member(request, group_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	if request.method == 'POST':
		form = GroupMembershipForm(request.POST)
		if form.is_valid():
			member = form.cleaned_data['scener_nick'].commit().releaser
			if not group.member_memberships.filter(member=member).count():
				membership = Membership(
					member=member,
					group=group,
					is_current=form.cleaned_data['is_current'])
				membership.save()
				group.updated_at = datetime.datetime.now()
				group.save()
				description = u"Added %s as a member of %s" % (member.name, group.name)
				Edit.objects.create(action_type='add_membership', focus=member, focus2=group,
					description=description, user=request.user)
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = GroupMembershipForm()
	return ajaxable_render(request, 'groups/add_member.html', {
		'html_title': "New member for %s" % group.name,
		'group': group,
		'form': form,
	})


@login_required
def remove_member(request, group_id, scener_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	scener = get_object_or_404(Releaser, is_group=False, id=scener_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			group.member_memberships.filter(member=scener).delete()
			group.updated_at = datetime.datetime.now()
			group.save()
			description = u"Removed %s as a member of %s" % (scener.name, group.name)
			Edit.objects.create(action_type='remove_membership', focus=scener, focus2=group,
				description=description, user=request.user)
		return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('group_remove_member', args=[group_id, scener_id]),
			"Are you sure you want to remove %s from the group %s?" % (scener.name, group.name),
			html_title="Removing %s from %s" % (scener.name, group.name))


@login_required
def edit_membership(request, group_id, membership_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	membership = get_object_or_404(Membership, group=group, id=membership_id)
	if request.method == 'POST':
		form = GroupMembershipForm(request.POST, initial={
			'scener_nick': membership.member.primary_nick,
			'is_current': membership.is_current,
		})
		if form.is_valid():
			member = form.cleaned_data['scener_nick'].commit().releaser
			# skip saving if the value of the member (scener) field duplicates an existing one on this group
			if not group.member_memberships.exclude(id=membership_id).filter(member=member).count():
				membership.member = member
				membership.is_current = form.cleaned_data['is_current']
				membership.save()
				group.updated_at = datetime.datetime.now()
				group.save()
				form.log_edit(request.user, member, group)

			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = GroupMembershipForm(initial={
			'scener_nick': membership.member.primary_nick,
			'is_current': membership.is_current,
		})
	return ajaxable_render(request, 'groups/edit_membership.html', {
		'html_title': "Editing %s's membership of %s" % (membership.member.name, group.name),
		'group': group,
		'membership': membership,
		'form': form,
	})


@login_required
def add_subgroup(request, group_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	if request.method == 'POST':
		form = GroupSubgroupForm(request.POST)
		if form.is_valid():
			member = form.cleaned_data['subgroup_nick'].commit().releaser
			if not group.member_memberships.filter(member=member).count():
				membership = Membership(
					member=member,
					group=group,
					is_current=form.cleaned_data['is_current'])
				membership.save()
				group.updated_at = datetime.datetime.now()
				group.save()
				description = u"Added %s as a subgroup of %s" % (member.name, group.name)
				Edit.objects.create(action_type='add_subgroup', focus=member, focus2=group,
					description=description, user=request.user)
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = GroupSubgroupForm()
	return ajaxable_render(request, 'groups/add_subgroup.html', {
		'html_title': "New subgroup for %s" % group.name,
		'group': group,
		'form': form,
	})


@login_required
def remove_subgroup(request, group_id, subgroup_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	subgroup = get_object_or_404(Releaser, is_group=True, id=subgroup_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			group.member_memberships.filter(member=subgroup).delete()
			group.updated_at = datetime.datetime.now()
			group.save()
			description = u"Removed %s as a subgroup of %s" % (subgroup.name, group.name)
			Edit.objects.create(action_type='remove_membership', focus=subgroup, focus2=group,
				description=description, user=request.user)
		return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('group_remove_subgroup', args=[group_id, subgroup_id]),
			"Are you sure you want to remove %s as a subgroup of %s?" % (subgroup.name, group.name),
			html_title="Removing %s from %s" % (subgroup.name, group.name))


@login_required
def edit_subgroup(request, group_id, membership_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	membership = get_object_or_404(Membership, group=group, id=membership_id)
	if request.method == 'POST':
		form = GroupSubgroupForm(request.POST)
		if form.is_valid():
			member = form.cleaned_data['subgroup_nick'].commit().releaser
			if not group.member_memberships.exclude(id=membership_id).filter(member=member).count():
				membership.member = member
				membership.is_current = form.cleaned_data['is_current']
				membership.save()
				group.updated_at = datetime.datetime.now()
				group.save()
				form.log_edit(request.user, member, group)
			return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		form = GroupSubgroupForm(initial={
			'subgroup_nick': membership.member.primary_nick,
			'is_current': membership.is_current,
		})
	return ajaxable_render(request, 'groups/edit_subgroup.html', {
		'html_title': "Editing %s as a subgroup of %s" % (membership.member.name, group.name),
		'group': group,
		'membership': membership,
		'form': form,
	})


@login_required
def convert_to_scener(request, group_id):
	group = get_object_or_404(Releaser, is_group=True, id=group_id)
	if not request.user.is_staff or not group.can_be_converted_to_scener():
		return HttpResponseRedirect(group.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):
			group.is_group = False
			group.updated_at = datetime.datetime.now()
			group.save()
			Edit.objects.create(action_type='convert_to_scener', focus=group,
				description=(u"Converted %s from a group to a scener" % group), user=request.user)
		return HttpResponseRedirect(group.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('group_convert_to_scener', args=[group_id]),
			"Are you sure you want to convert %s into a scener?" % (group.name),
			html_title="Converting %s to a scener" % (group.name))
