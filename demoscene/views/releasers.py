from demoscene.shortcuts import *
from demoscene.models import Releaser, Production, Nick, Credit, Edit
from demoscene.forms.releaser import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime


@login_required
def add_credit(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if request.method == 'POST':
		form = ReleaserAddCreditForm(releaser, request.POST)
		if form.is_valid():
			production = Production.objects.get(id=form.cleaned_data['production_id'])
			credit = Credit(
				production=production,
				nick=form.cleaned_data['nick'],
				role=form.cleaned_data['role']
			)
			credit.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.log_creation(request.user, production, releaser)

			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser)

	return ajaxable_render(request, 'releasers/add_credit.html', {
		'html_title': "Add credit for %s" % releaser.name,
		'releaser': releaser,
		'form': form,
	})


@login_required
def edit_credit(request, releaser_id, credit_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	credit = get_object_or_404(Credit, nick__releaser=releaser, id=credit_id)
	if request.method == 'POST':
		form = ReleaserAddCreditForm(releaser, request.POST, initial={
			'nick': credit.nick_id,
			'production_id': credit.production_id,
			'production_name': credit.production.title,
			'role': credit.role
		})
		if form.is_valid():
			production = Production.objects.get(id=form.cleaned_data['production_id'])
			credit.production = production
			credit.nick = form.cleaned_data['nick']
			credit.role = form.cleaned_data['role']
			credit.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.log_edit(request.user, production, releaser)

			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser, {
			'nick': credit.nick_id,
			'production_id': credit.production_id,
			'production_name': credit.production.title,
			'role': credit.role
		})
	return ajaxable_render(request, 'releasers/edit_credit.html', {
		'html_title': "Editing credit for %s" % credit.production.title,
		'releaser': releaser,
		'credit': credit,
		'form': form,
	})


@login_required
def delete_credit(request, releaser_id, credit_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	credit = get_object_or_404(Credit, nick__releaser=releaser, id=credit_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			production = credit.production
			credit.delete()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			Edit.objects.create(action_type='delete_credit', focus=production, focus2=releaser,
				description=("Deleted %s's credit on %s" % (credit.nick, production)), user=request.user)
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('releaser_delete_credit', args=[releaser_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, credit.production.title),
			html_title="Deleting %s's credit from %s" % (credit.nick.name, credit.production.title))


@login_required
def edit_notes(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(releaser.get_absolute_edit_url())

	def success(form):
		form.log_edit(request.user)

	return simple_ajax_form(request, 'releaser_edit_notes', releaser, ReleaserEditNotesForm,
		title='Editing notes for %s' % releaser.name,
		update_datestamp=True, on_success=success)


@login_required
def edit_nick(request, releaser_id, nick_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	primary_nick = releaser.primary_nick
	if releaser.is_group:
		nick_form_class = GroupNickForm
	else:
		nick_form_class = ScenerNickForm
	nick = get_object_or_404(Nick, releaser=releaser, id=nick_id)
	if request.method == 'POST':
		form = nick_form_class(releaser, request.POST, instance=nick, for_admin=request.user.is_staff)
		if form.is_valid():
			form.save()
			if form.cleaned_data.get('override_primary_nick') or nick == primary_nick:
				releaser.name = nick.name
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			form.log_edit(request.user)
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser, instance=nick, for_admin=request.user.is_staff)

	return ajaxable_render(request, 'releasers/edit_nick_form.html', {
		'form': form,
		'nick': nick,
		'html_title': "Editing name: %s" % nick.name,
		'title': "Editing name: %s" % nick.name,
		'action_url': reverse('releaser_edit_nick', args=[releaser.id, nick.id]),
	})


@login_required
def add_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if releaser.is_group:
		nick_form_class = GroupNickForm
	else:
		nick_form_class = ScenerNickForm

	if request.method == 'POST':
		nick = Nick(releaser=releaser)
		form = nick_form_class(releaser, request.POST, instance=nick, for_admin=request.user.is_staff)
		if form.is_valid():
			form.save()
			if form.cleaned_data.get('override_primary_nick'):
				releaser.name = nick.name
				releaser.save()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			form.log_creation(request.user)
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser, for_admin=request.user.is_staff)

	return ajaxable_render(request, 'releasers/nick_form.html', {
		'form': form,
		'title': "Adding another nick for %s" % releaser.name,
		'html_title': "Adding another nick for %s" % releaser.name,
		'action_url': reverse('releaser_add_nick', args=[releaser.id]),
	})


@login_required
def edit_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	return ajaxable_render(request, 'releasers/confirm_edit_nick.html', {
		'html_title': "Editing %s's name" % releaser.name,
		'releaser': releaser,
	})


@login_required
def change_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if request.method == 'POST':
		nick = get_object_or_404(Nick, releaser=releaser, id=request.POST['nick_id'])
		releaser.name = nick.name
		releaser.updated_at = datetime.datetime.now()
		releaser.save()
		Edit.objects.create(action_type='change_primary_nick', focus=releaser,
			description=("Set primary nick to '%s'" % nick.name), user=request.user)
	return HttpResponseRedirect(releaser.get_absolute_edit_url())


@login_required
def delete_nick(request, releaser_id, nick_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	nick = get_object_or_404(Nick, releaser=releaser, id=nick_id)
	if nick.is_primary_nick():  # not allowed to delete primary nick
		return HttpResponseRedirect(releaser.get_absolute_edit_url())

	if request.method == 'POST':
		if request.POST.get('yes'):
			nick.reassign_references_and_delete()
			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			Edit.objects.create(action_type='delete_nick', focus=releaser,
				description=("Deleted nick '%s'" % nick.name), user=request.user)
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		if nick.is_referenced():
			prompt = """
				Are you sure you want to delete %s's alternative name '%s'?
				This will cause all releases under the name '%s' to be reassigned back to '%s'.
			""" % (releaser.name, nick.name, nick.name, releaser.name)
		else:
			prompt = "Are you sure you want to delete %s's alternative name '%s'?" % (releaser.name, nick.name)

		return simple_ajax_confirmation(request,
			reverse('releaser_delete_nick', args=[releaser_id, nick_id]),
			prompt,
			html_title="Deleting name: %s" % nick.name)


@login_required
def delete(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):

			# insert log entry before actually deleting, so that it doesn't try to
			# insert a null ID for the focus field
			if releaser.is_group:
				Edit.objects.create(action_type='delete_group', focus=releaser,
					description=("Deleted group '%s'" % releaser.name), user=request.user)
			else:
				Edit.objects.create(action_type='delete_scener', focus=releaser,
					description=("Deleted scener '%s'" % releaser.name), user=request.user)

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
			reverse('delete_releaser', args=[releaser_id]),
			"Are you sure you want to delete %s?" % releaser.name,
			html_title="Deleting %s" % releaser.name)


@login_required
def edit_external_links(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)

	if request.method == 'POST':
		formset = ReleaserExternalLinkFormSet(request.POST, instance=releaser)
		if formset.is_valid():
			formset.save()
			formset.log_edit(request.user, 'releaser_edit_external_links')

			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		formset = ReleaserExternalLinkFormSet(instance=releaser)
	return ajaxable_render(request, 'releasers/edit_external_links.html', {
		'html_title': "Editing external links for %s" % releaser.name,
		'releaser': releaser,
		'formset': formset,
	})
