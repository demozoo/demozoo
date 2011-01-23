from demoscene.shortcuts import *
from demoscene.models import Releaser, Production, Nick, Credit
from demoscene.forms.releaser import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

@login_required
def add_credit(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if request.method == 'POST':
		form = ReleaserAddCreditForm(releaser, request.POST)
		if form.is_valid():
			production = Production.objects.get(id = form.cleaned_data['production_id'])
			credit = Credit(
				production = production,
				nick = form.cleaned_data['nick_id'],
				role = form.cleaned_data['role']
			)
			credit.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser)
	
	return ajaxable_render(request, 'releasers/add_credit.html', {
		'releaser': releaser,
		'form': form,
	})

@login_required
def edit_credit(request, releaser_id, credit_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	credit = get_object_or_404(Credit, nick__releaser = releaser, id = credit_id)
	if request.method == 'POST':
		form = ReleaserAddCreditForm(releaser, request.POST)
		if form.is_valid():
			production = Production.objects.get(id = form.cleaned_data['production_id'])
			credit.production = production
			credit.nick = form.cleaned_data['nick_id']
			credit.role = form.cleaned_data['role']
			credit.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser, {
			'nick_id': credit.nick_id,
			'production_id': credit.production_id,
			'production_name': credit.production.title,
			'role': credit.role
		})
	return ajaxable_render(request, 'releasers/edit_credit.html', {
		'releaser': releaser,
		'credit': credit,
		'form': form,
	})

@login_required
def delete_credit(request, releaser_id, credit_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	credit = get_object_or_404(Credit, nick__releaser = releaser, id = credit_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			production = credit.production
			credit.delete()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('releaser_delete_credit', args = [releaser_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, credit.production.title) )

@login_required
def edit_notes(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	return simple_ajax_form(request, 'releaser_edit_notes', releaser, ReleaserEditNotesForm,
		title = 'Editing notes for %s' % releaser.name,
		update_datestamp = True)

@login_required
def edit_nick(request, releaser_id, nick_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	primary_nick = releaser.primary_nick
	if releaser.is_group:
		nick_form_class = GroupNickForm
	else:
		nick_form_class = ScenerNickForm
	nick = get_object_or_404(Nick, releaser = releaser, id = nick_id)
	if request.method == 'POST':
		form = nick_form_class(releaser, request.POST, instance = nick)
		if form.is_valid():
			form.save()
			if form.cleaned_data.get('override_primary_nick') or nick == primary_nick:
				releaser.name = nick.name
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser, instance = nick)
	
	return ajaxable_render(request, 'releasers/edit_nick_form.html', {
		'form': form,
		'nick': nick,
		'title': "Editing name: %s" % nick.name,
		'action_url': reverse('releaser_edit_nick', args = [releaser.id, nick.id]),
	})

@login_required
def add_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if releaser.is_group:
		nick_form_class = GroupNickForm
	else:
		nick_form_class = ScenerNickForm
	
	if request.method == 'POST':
		nick = Nick(releaser = releaser)
		form = nick_form_class(releaser, request.POST, instance = nick)
		if form.is_valid():
			form.save()
			if form.cleaned_data.get('override_primary_nick'):
				releaser.name = nick.name
				releaser.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser)
	
	return ajaxable_render(request, 'releasers/nick_form.html', {
		'form': form,
		'title': "Adding another nick for %s" % releaser.name,
		'action_url': reverse('releaser_add_nick', args = [releaser.id]),
	})

@login_required
def edit_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	return ajaxable_render(request, 'releasers/confirm_edit_nick.html', {
		'releaser': releaser,
	})

@login_required
def change_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if request.method == 'POST':
		nick = get_object_or_404(Nick, releaser = releaser, id = request.POST['nick_id'])
		releaser.name = nick.name
		releaser.updated_at = datetime.datetime.now()
		releaser.save()
	return HttpResponseRedirect(releaser.get_absolute_edit_url())

@login_required
def delete_nick(request, releaser_id, nick_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	nick = get_object_or_404(Nick, releaser = releaser, id = nick_id)
	if nick.is_referenced():
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	
	if request.method == 'POST':
		if request.POST.get('yes'):
			nick.delete()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('releaser_delete_nick', args = [releaser_id, nick_id]),
			"Are you sure you want to delete %s's alternative name '%s'?" % (releaser.name, nick.name) )

@login_required
def delete(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):
			releaser.delete()
			messages.success(request, "'%s' deleted" % releaser.name)
			if releaser.is_group:
				return HttpResponseRedirect(reverse('groups'))
			else:
				return HttpResponseRedirect(reverse('sceners'))
		else:
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_releaser', args = [releaser_id]),
			"Are you sure you want to delete %s?" % releaser.name )
