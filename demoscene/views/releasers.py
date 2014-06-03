from __future__ import absolute_import  # ensure that 'from productions.* import...' works relative to the productions app, not views.productions

from demoscene.shortcuts import get_object_or_404, HttpResponseRedirect, render, simple_ajax_confirmation, reverse, simple_ajax_form
from demoscene.models import Releaser, Nick, Edit
from productions.models import Production, Credit
from demoscene.forms.releaser import ReleaserCreditForm, ReleaserEditNotesForm, GroupNickForm, ScenerNickForm, ReleaserExternalLinkFormSet
from demoscene.forms.common import CreditFormSet
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime
from read_only_mode import writeable_site_required


@writeable_site_required
@login_required
def add_credit(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if request.method == 'POST':
		form = ReleaserCreditForm(releaser, request.POST)
		credit_formset = CreditFormSet(request.POST, queryset=Credit.objects.none(), prefix="credit")
		if form.is_valid() and credit_formset.is_valid():
			production = Production.objects.get(id=form.cleaned_data['production_id'])
			credits = credit_formset.save(commit=False)
			if credits:
				nick = form.cleaned_data['nick']
				for credit in credits:
					credit.nick = nick
					credit.production = production
					credit.save()

				production.updated_at = datetime.datetime.now()
				production.has_bonafide_edits = True
				production.save()
				releaser.updated_at = datetime.datetime.now()
				releaser.save()
				credits_description = ', '.join([credit.description for credit in credits])
				description = (u"Added credit for %s on %s: %s" % (nick, production, credits_description))
				Edit.objects.create(action_type='add_credit', focus=production,
					focus2=nick.releaser,
					description=description, user=request.user)
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserCreditForm(releaser)
		credit_formset = CreditFormSet(queryset=Credit.objects.none(), prefix="credit")

	return render(request, 'releasers/add_credit.html', {
		'releaser': releaser,
		'form': form,
		'credit_formset': credit_formset,
	})


@writeable_site_required
@login_required
def edit_credit(request, releaser_id, nick_id, production_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	nick = get_object_or_404(Nick, releaser=releaser, id=nick_id)
	production = get_object_or_404(Production, id=production_id)
	credits = Credit.objects.filter(nick=nick, production=production)

	if request.method == 'POST':
		form = ReleaserCreditForm(releaser, request.POST, initial={
			'nick': nick.id,
			'production_id': production.id,
			'production_name': production.title,
		})
		credit_formset = CreditFormSet(request.POST, queryset=credits, prefix="credit")

		if form.is_valid() and credit_formset.is_valid():
			production = Production.objects.get(id=form.cleaned_data['production_id'])
			updated_credits = credit_formset.save(commit=False)

			# make sure that each credit has production and nick populated
			for credit in updated_credits:
				credit.nick = nick
				credit.production = production
				credit.save()

			new_nick = form.cleaned_data['nick']
			if form.changed_data:
				# need to update the production / nick field of all credits in the set
				# (not just the ones that have been updated by credit_formset.save)
				credits.update(nick=new_nick, production=production)

			releaser.updated_at = datetime.datetime.now()
			releaser.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()

			new_credits = Credit.objects.filter(nick=new_nick, production=production)
			credits_description = ', '.join([credit.description for credit in new_credits])
			Edit.objects.create(action_type='edit_credit', focus=production,
				focus2=releaser,
				description=(u"Updated %s's credit on %s: %s" % (new_nick, production, credits_description)),
				user=request.user)

			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserCreditForm(releaser, {
			'nick': nick.id,
			'production_id': production.id,
			'production_name': production.title,
		})
		credit_formset = CreditFormSet(queryset=credits, prefix="credit")
	return render(request, 'releasers/edit_credit.html', {
		'releaser': releaser,
		'nick': nick,
		'production': production,
		'form': form,
		'credit_formset': credit_formset,
	})


@writeable_site_required
@login_required
def delete_credit(request, releaser_id, nick_id, production_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	nick = get_object_or_404(Nick, releaser=releaser, id=nick_id)
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			credits = Credit.objects.filter(nick=nick, production=production)
			if credits:
				credits.delete()
				releaser.updated_at = datetime.datetime.now()
				releaser.save()
				production.updated_at = datetime.datetime.now()
				production.has_bonafide_edits = True
				production.save()
				Edit.objects.create(action_type='delete_credit', focus=production, focus2=releaser,
					description=(u"Deleted %s's credit on %s" % (nick, production)), user=request.user)
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('releaser_delete_credit', args=[releaser_id, nick_id, production_id]),
			"Are you sure you want to delete %s's credit from %s?" % (nick.name, production.title),
			html_title="Deleting %s's credit from %s" % (nick.name, production.title))


@writeable_site_required
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


@writeable_site_required
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
			return HttpResponseRedirect(releaser.get_absolute_edit_url() + "?editing=nicks")
	else:
		form = nick_form_class(releaser, instance=nick, for_admin=request.user.is_staff)

	return render(request, 'releasers/edit_nick_form.html', {
		'form': form,
		'nick': nick,
		'title': "Editing name: %s" % nick.name,
		'action_url': reverse('releaser_edit_nick', args=[releaser.id, nick.id]),
	})


@writeable_site_required
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
			return HttpResponseRedirect(releaser.get_absolute_edit_url() + "?editing=nicks")
	else:
		form = nick_form_class(releaser, for_admin=request.user.is_staff)

	return render(request, 'releasers/add_nick_form.html', {
		'form': form,
		'title': "Adding another nick for %s" % releaser.name,
		'action_url': reverse('releaser_add_nick', args=[releaser.id]),
	})


@writeable_site_required
@login_required
def edit_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	return render(request, 'releasers/confirm_edit_nick.html', {
		'releaser': releaser,
	})


@writeable_site_required
@login_required
def change_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if request.method == 'POST':
		nick = get_object_or_404(Nick, releaser=releaser, id=request.POST['nick_id'])
		releaser.name = nick.name
		releaser.updated_at = datetime.datetime.now()
		releaser.save()
		Edit.objects.create(action_type='change_primary_nick', focus=releaser,
			description=(u"Set primary nick to '%s'" % nick.name), user=request.user)
	return HttpResponseRedirect(releaser.get_absolute_edit_url() + "?editing=nicks")


@writeable_site_required
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
				description=(u"Deleted nick '%s'" % nick.name), user=request.user)
		return HttpResponseRedirect(releaser.get_absolute_edit_url() + "?editing=nicks")
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


@writeable_site_required
@login_required
def delete(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):

			# insert log entry before actually deleting, so that it doesn't try to
			# insert a null ID for the focus field
			if releaser.is_group:
				Edit.objects.create(action_type='delete_group', focus=releaser,
					description=(u"Deleted group '%s'" % releaser.name), user=request.user)
			else:
				Edit.objects.create(action_type='delete_scener', focus=releaser,
					description=(u"Deleted scener '%s'" % releaser.name), user=request.user)

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


@writeable_site_required
@login_required
def edit_external_links(request, releaser_id):
	releaser = get_object_or_404(Releaser, id=releaser_id)

	if request.method == 'POST':
		formset = ReleaserExternalLinkFormSet(request.POST, instance=releaser)
		if formset.is_valid():
			formset.save_ignoring_uniqueness()
			formset.log_edit(request.user, 'releaser_edit_external_links')

			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		formset = ReleaserExternalLinkFormSet(instance=releaser)
	return render(request, 'releasers/edit_external_links.html', {
		'releaser': releaser,
		'formset': formset,
	})
