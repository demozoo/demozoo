from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, Membership
from demoscene.forms.releaser import *

from django.contrib.auth.decorators import login_required
import datetime

def index(request):
	
	nick_page = get_page(
		Nick.objects.filter(releaser__is_group = False).extra(
			select={'lower_name': 'lower(demoscene_nick.name)'}
		).order_by('lower_name'),
		request.GET.get('page', '1') )
	
	return render(request, 'sceners/index.html', {
		'nick_page': nick_page,
	})

def show(request, scener_id, edit_mode = False):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'sceners/show.html', {
		'scener': scener,
		'productions': scener.productions().order_by('-release_date_date', '-title'),
		'credits': scener.credits().order_by('-production__release_date_date', '-production__title'),
		'memberships': scener.group_memberships.all().select_related('group').order_by('-is_current', 'group__name'),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})

@login_required
def edit(request, scener_id):
	set_edit_mode_active(True, request.user)
	return show(request, scener_id, edit_mode = True)

def edit_done(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(scener.get_absolute_url())

@login_required
def edit_external_links(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
		
	return simple_ajax_form(request, 'scener_edit_external_links', scener, ScenerEditExternalLinksForm,
		title = 'Editing external links for %s:' % scener.name,
		html_form_class = 'external_links_form',
		update_datestamp = True)
		
@login_required
def edit_location(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	
	return simple_ajax_form(request, 'scener_edit_location', scener, ScenerEditLocationForm,
		title = 'Editing location for %s:' % scener.name,
		update_datestamp = True)

@login_required
def edit_real_name(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(scener.get_absolute_edit_url())
		
	return simple_ajax_form(request, 'scener_edit_real_name', scener, ScenerEditRealNameForm,
		title = "Editing %s's real name:" % scener.name,
		update_datestamp = True)

@login_required
def create(request):
	if request.method == 'POST':
		scener = Releaser(is_group = False, updated_at = datetime.datetime.now())
		form = CreateScenerForm(request.POST, instance = scener)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		form = CreateScenerForm()
	
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'html_title': "New scener",
		'title': "New scener",
		'action_url': reverse('new_scener'),
	})

@login_required
def add_group(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		form = ScenerMembershipForm(request.POST)
		if form.is_valid():
			group = form.cleaned_data['group_nick'].commit().releaser
			if not scener.group_memberships.filter(group = group).count():
				membership = Membership(
					member = scener,
					group = form.cleaned_data['group_nick'].commit().releaser,
					is_current = form.cleaned_data['is_current'])
				membership.save()
				scener.updated_at = datetime.datetime.now()
				scener.save()
			return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		form = ScenerMembershipForm()
	
	return ajaxable_render(request, 'sceners/add_group.html', {
		'html_title': "New group for %s" % scener.name,
		'scener': scener,
		'form': form,
	})

@login_required
def remove_group(request, scener_id, group_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			scener.group_memberships.filter(group = group).delete()
			scener.updated_at = datetime.datetime.now()
			scener.save()
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('scener_remove_group', args = [scener_id, group_id]),
			"Are you sure you want to remove %s from the group %s?" % (scener.name, group.name),
			html_title = "Removing %s from %s" % (scener.name, group.name) )

@login_required
def edit_membership(request, scener_id, membership_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	membership = get_object_or_404(Membership, member = scener, id = membership_id)
	if request.method == 'POST':
		form = ScenerMembershipForm(request.POST)
		if form.is_valid():
			group = form.cleaned_data['group_nick'].commit().releaser
			if not scener.group_memberships.exclude(id = membership_id).filter(group = group).count():
				membership.group = group
				membership.is_current = form.cleaned_data['is_current']
				membership.save()
				scener.updated_at = datetime.datetime.now()
				scener.save()
			return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		form = ScenerMembershipForm(initial = {
			'group_nick': membership.group.primary_nick,
			'is_current': membership.is_current,
		})
	return ajaxable_render(request, 'sceners/edit_membership.html', {
		'html_title': "Editing %s's membership of %s" % (scener.name, membership.group.name),
		'scener': scener,
		'membership': membership,
		'form': form,
	})

@login_required
def convert_to_group(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if not request.user.is_staff or not scener.can_be_converted_to_group():
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):
			scener.is_group = True
			scener.updated_at = datetime.datetime.now()
			scener.save()
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('scener_convert_to_group', args = [scener_id]),
			"Are you sure you want to convert %s into a group?" % (scener.name),
			html_title = "Converting %s to a group" % (scener.name) )
