from demoscene.shortcuts import *
from demoscene.models import Releaser, NickVariant, Production, Nick, Credit
from demoscene.forms import ReleaserAddCreditForm, ReleaserEditNotesForm, ScenerNickForm, GroupNickForm
from django.contrib.auth.decorators import login_required

def autocomplete(request):
	query = request.GET.get('q')
	new_option = request.GET.get('new_option', False)
	nick_variants = NickVariant.autocompletion_search(query,
		limit = request.GET.get('limit', 10),
		exact = request.GET.get('exact', False),
		groups = request.GET.getlist('group[]')
	)
	return render(request, 'releasers/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')

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
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser)
	if request.is_ajax():
		template = 'releasers/add_credit.html'
	else:
		template = 'releasers/add_credit_page.html'
	return render(request, template, {
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
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = ReleaserAddCreditForm(releaser, {
			'nick_id': credit.nick_id,
			'production_id': credit.production_id,
			'production_name': credit.production.title,
			'role': credit.role
		})
	if request.is_ajax():
		template = 'releasers/edit_credit.html'
	else:
		template = 'releasers/edit_credit_page.html'
	return render(request, template, {
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
			credit.delete()
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		if request.is_ajax():
			template = 'releasers/delete_credit.html'
		else:
			template = 'releasers/delete_credit_page.html'
		return render(request, template, {
			'releaser': releaser,
			'credit': credit,
		})

@login_required
def edit_notes(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(releaser.get_absolute_edit_url())
	return simple_ajax_form(request, 'releaser_edit_notes', releaser, ReleaserEditNotesForm,
		title = 'Editing notes for %s' % releaser.name)

@login_required
def edit_nick(request, releaser_id, nick_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if releaser.is_group:
		nick_form_class = GroupNickForm
	else:
		nick_form_class = ScenerNickForm
	nick = get_object_or_404(Nick, releaser = releaser, id = nick_id)
	if request.method == 'POST':
		form = nick_form_class(releaser, request.POST, instance = nick)
		if form.is_valid():
			form.save()
			if form.cleaned_data['override_primary_nick']:
				releaser.name = nick.name
				releaser.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser, instance = nick)
	if request.is_ajax():
		template = 'releasers/nick_form.html'
	else:
		template = 'releasers/nick_form_page.html'
	
	return render(request, template, {
		'form': form,
		'title': "Editing nick: %s" % nick.name,
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
			if form.cleaned_data['override_primary_nick']:
				releaser.name = nick.name
				releaser.save()
			return HttpResponseRedirect(releaser.get_absolute_edit_url())
	else:
		form = nick_form_class(releaser)
	if request.is_ajax():
		template = 'releasers/nick_form.html'
	else:
		template = 'releasers/nick_form_page.html'
	
	return render(request, template, {
		'form': form,
		'title': "Adding another nick for %s" % releaser.name,
		'action_url': reverse('releaser_add_nick', args = [releaser.id]),
	})

@login_required
def edit_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if request.is_ajax():
		template = 'releasers/confirm_edit_nick.html'
	else:
		template = 'releasers/confirm_edit_nick_page.html'
	return render(request, template, {
		'releaser': releaser,
	})

@login_required
def change_primary_nick(request, releaser_id):
	releaser = get_object_or_404(Releaser, id = releaser_id)
	if request.method == 'POST':
		nick = get_object_or_404(Nick, releaser = releaser, id = request.POST['nick_id'])
		releaser.name = nick.name
		releaser.save()
	return HttpResponseRedirect(releaser.get_absolute_edit_url())
