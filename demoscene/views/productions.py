from demoscene.shortcuts import *
from demoscene.models import Production, Byline, Credit, Nick, Screenshot, ProductionLink, Edit
from demoscene.forms.production import *
from demoscene.forms.common import CreditFormSet
from taggit.models import Tag
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import ValidationError
import datetime
from django.utils import simplejson as json
from screenshots.tasks import capture_upload_for_processing


def index(request, supertype):
	queryset = Production.objects.filter(supertype=supertype)

	order = request.GET.get('order', 'title')

	if supertype == 'production':
		title = "Productions"
		add_item_url = reverse('new_production')
		add_item_text = "New production"
		menu_section = "productions"
	elif supertype == 'graphics':
		title = "Graphics"
		add_item_url = reverse('new_graphics')
		add_item_text = "New graphics"
		menu_section = "graphics"
	else:  # supertype == 'music'
		title = "Music"
		add_item_url = reverse('new_music')
		add_item_text = "New music"
		menu_section = "music"

	queryset = apply_order(queryset, order)

	production_page = get_page(
		queryset,
		request.GET.get('page', '1'))

	return render(request, 'productions/index.html', {
		'title': title,
		'order': order,
		'add_item_url': add_item_url,
		'add_item_text': add_item_text,
		'production_page': production_page,
		'menu_section': menu_section
	})


def tagged(request, tag_slug, supertype):
	try:
		tag = Tag.objects.get(slug=tag_slug)
	except Tag.DoesNotExist:
		tag = Tag(name=tag_slug)
	queryset = Production.objects.filter(supertype=supertype, tags__slug=tag_slug)

	order = request.GET.get('order', 'title')

	if supertype == 'production':
		title = "Productions tagged '%s'" % tag.name
	elif supertype == 'graphics':
		title = "Graphics tagged '%s'" % tag.name
	else:  # supertype == 'music'
		title = "Music tagged '%s'" % tag.name

	queryset = apply_order(queryset, order)

	production_page = get_page(
		queryset,
		request.GET.get('page', '1'))

	return render(request, 'productions/index.html', {
		'title': title,
		'production_page': production_page,
		'order': order,
	})


def apply_order(queryset, order):
	if order == 'date':
		return queryset.order_by('release_date_date')
	else:  # title
		return queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title')


def show(request, production_id, edit_mode=False):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'production':
		return HttpResponseRedirect(production.get_absolute_url())

	edit_mode = edit_mode or sticky_editing_active(request.user)

	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name', 'category'),
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.links.filter(is_download_link=True),
		'external_links': production.links.filter(is_download_link=False),
		'soundtracks': [
			link.soundtrack for link in
			production.soundtrack_links.order_by('position').select_related('soundtrack')
		],
		'competition_placings': production.competition_placings.order_by('competition__party__start_date_date'),
		'invitation_parties': production.invitation_parties.order_by('start_date_date'),
		'tags': production.tags.all(),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})


@login_required
def edit(request, production_id):
	set_edit_mode_active(True, request.user)
	return show(request, production_id, edit_mode=True)


def edit_done(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(production.get_absolute_url())


def history(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'production':
		return HttpResponseRedirect(production.get_history_url())
	return render(request, 'productions/history.html', {
		'production': production,
		'edits': Edit.for_model(production),
	})


@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id=production_id)

	use_invitation_formset = False
	invitation_formset = None

	if production.supertype == 'production':
		form_class = ProductionEditCoreDetailsForm
		use_invitation_formset = True
	elif production.supertype == 'graphics':
		form_class = GraphicsEditCoreDetailsForm
	else:  # production.supertype == 'music':
		form_class = MusicEditCoreDetailsForm

	if request.method == 'POST':
		form = form_class(request.POST, instance=production)

		if use_invitation_formset:
			invitation_formset = ProductionInvitationPartyFormset(request.POST, initial=[
				{'party': party}
				for party in production.invitation_parties.order_by('start_date_date')
			])

		if form.is_valid() and ((not use_invitation_formset) or invitation_formset.is_valid()):
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			form.save()

			edit_descriptions = []
			main_edit_description = form.changed_data_description
			if main_edit_description:
				edit_descriptions.append(main_edit_description)

			if use_invitation_formset:
				invitation_parties = [party_form.cleaned_data['party'].commit()
					for party_form in invitation_formset.forms
					if party_form.cleaned_data.get('party') and party_form not in invitation_formset.deleted_forms]
				production.invitation_parties = invitation_parties

				if invitation_formset.has_changed():
					party_names = [party.name for party in invitation_parties]
					if party_names:
						edit_descriptions.append(
							u"Set invitation for %s" % (u", ".join(party_names))
						)
					else:
						edit_descriptions.append(u"Unset as invitation")

			if edit_descriptions:
				Edit.objects.create(action_type='edit_production_core_details', focus=production,
					description=u"; ".join(edit_descriptions), user=request.user)

			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = form_class(instance=production)

		if use_invitation_formset:
			invitation_formset = ProductionInvitationPartyFormset(initial=[
				{'party': party}
				for party in production.invitation_parties.order_by('start_date_date')
			])

	return ajaxable_render(request, 'productions/edit_core_details.html', {
		'html_title': "Editing %s: %s" % (production.supertype, production.title),
		'production': production,
		'form': form,
		'invitation_formset': invitation_formset,
	})


@login_required
def edit_notes(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())

	def success(form):
		form.log_edit(request.user)

	return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
		title='Editing notes for %s:' % production.title,
		update_datestamp=True, update_bonafide_flag=True, on_success=success)


@login_required
def edit_external_links(request, production_id):
	production = get_object_or_404(Production, id=production_id)

	if request.method == 'POST':
		formset = ProductionExternalLinkFormSet(request.POST, instance=production, queryset=production.links.filter(is_download_link=False))
		if formset.is_valid():
			formset.save()
			formset.log_edit(request.user, 'production_edit_external_links')
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()

			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionExternalLinkFormSet(instance=production, queryset=production.links.filter(is_download_link=False))
	return ajaxable_render(request, 'productions/edit_external_links.html', {
		'html_title': "Editing external links for %s" % production.title,
		'production': production,
		'formset': formset,
	})


@login_required
def add_download_link(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	production_link = ProductionLink(production=production, is_download_link=True)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance=production_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			Edit.objects.create(action_type='add_download_link', focus=production,
				description=(u"Added download link %s" % production_link.url), user=request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance=production_link)
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Adding download link for %s:" % production.title,
		'html_title': "Adding download link for %s" % production.title,
		'action_url': reverse('production_add_download_link', args=[production.id]),
	})


@login_required
def edit_download_link(request, production_id, production_link_id):
	production = get_object_or_404(Production, id=production_id)
	production_link = get_object_or_404(ProductionLink, id=production_link_id, production=production, is_download_link=True)
	original_url = production_link.url
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance=production_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			Edit.objects.create(action_type='edit_download_link', focus=production,
				description=(u"Updated download link from %s to %s" % (original_url, production_link.url)), user=request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance=production_link)
	return ajaxable_render(request, 'productions/edit_download_link.html', {
		'html_title': "Editing download link for %s" % production.title,
		'form': form,
		'production': production,
		'production_link': production_link,
	})


@login_required
def delete_download_link(request, production_id, production_link_id):
	production = get_object_or_404(Production, id=production_id)
	production_link = get_object_or_404(ProductionLink, id=production_link_id, production=production, is_download_link=True)
	if request.method == 'POST':
		if request.POST.get('yes'):
			production_link.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			Edit.objects.create(action_type='delete_download_link', focus=production,
				description=(u"Deleted download link %s" % production_link.url), user=request.user)
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_download_link', args=[production_id, production_link_id]),
			"Are you sure you want to delete this download link for %s?" % production.title,
			html_title="Deleting download link for %s" % production.title)


@login_required
def screenshots(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	return render(request, 'productions/screenshots.html', {
		'production': production,
		'screenshots': production.screenshots.order_by('id'),
	})


@login_required
def add_screenshot(request, production_id):
	return HttpResponse('screenshot uploading temporarily disabled because I broke it. Sorry, will fix asap... - gasman 2013-02-09')
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		uploaded_files = request.FILES.getlist('screenshot')
		file_count = len(uploaded_files)
		for f in uploaded_files:
			screenshot = Screenshot.objects.create(production=production)
			capture_upload_for_processing(f, screenshot.id)

		if file_count:
			# at least one screenshot was uploaded
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()

			if file_count == 1:
				Edit.objects.create(action_type='add_screenshot', focus=production,
					description=("Added screenshot"), user=request.user)
			else:
				Edit.objects.create(action_type='add_screenshot', focus=production,
					description=("Added %s screenshots" % file_count), user=request.user)

		return HttpResponseRedirect(production.get_absolute_edit_url())
	return ajaxable_render(request, 'productions/add_screenshot.html', {
		'html_title': "Adding screenshots for %s" % production.title,
		'production': production,
	})


@login_required
def delete_screenshot(request, production_id, screenshot_id):
	production = get_object_or_404(Production, id=production_id)
	screenshot = get_object_or_404(Screenshot, id=screenshot_id, production=production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			screenshot.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			Edit.objects.create(action_type='delete_screenshot', focus=production,
				description="Deleted screenshot", user=request.user)
		return HttpResponseRedirect(reverse('production_screenshots', args=[production.id]))
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_screenshot', args=[production_id, screenshot_id]),
			"Are you sure you want to delete this screenshot for %s?" % production.title,
			html_title="Deleting screenshot for %s" % production.title)


@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at=datetime.datetime.now())
		form = CreateProductionForm(request.POST, instance=production)
		download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			form.log_creation(request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateProductionForm(initial={
			'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
		})
		download_link_formset = ProductionDownloadLinkFormSet()
	return ajaxable_render(request, 'productions/create.html', {
		'html_title': "New production",
		'form': form,
		'download_link_formset': download_link_formset,
	})


@login_required
def add_credit(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		nick_form = ProductionCreditedNickForm(request.POST)
		credit_formset = CreditFormSet(request.POST, queryset=Credit.objects.none(), prefix="credit")
		if nick_form.is_valid() and credit_formset.is_valid():
			credits = credit_formset.save(commit=False)
			if credits:
				nick = nick_form.cleaned_data['nick'].commit()
				for credit in credits:
					credit.nick = nick
					credit.production = production
					credit.save()
				credits_description = ', '.join([credit.description for credit in credits])
				description = (u"Added credit for %s on %s: %s" % (nick, production, credits_description))
				Edit.objects.create(action_type='add_credit', focus=production,
					focus2=nick.releaser,
					description=description, user=request.user)

			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			# form.log_creation(request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		nick_form = ProductionCreditedNickForm()
		credit_formset = CreditFormSet(queryset=Credit.objects.none(), prefix="credit")
	return ajaxable_render(request, 'productions/add_credit.html', {
		'html_title': "Adding credit for %s" % production.title,
		'production': production,
		'nick_form': nick_form,
		'credit_formset': credit_formset,
	})


@login_required
def edit_credit(request, production_id, nick_id):
	production = get_object_or_404(Production, id=production_id)
	nick = get_object_or_404(Nick, id=nick_id)
	credits = production.credits.filter(nick=nick)
	if request.method == 'POST':
		nick_form = ProductionCreditedNickForm(request.POST, nick=nick)
		credit_formset = CreditFormSet(request.POST, queryset=credits, prefix="credit")
		if nick_form.is_valid() and credit_formset.is_valid():
			updated_credits = credit_formset.save(commit=False)
			# make sure that each credit has production and nick populated
			for credit in updated_credits:
				credit.nick = nick
				credit.production = production
				credit.save()

			if 'nick' in nick_form.changed_data:
				# need to update the nick field of all credits in the set
				# (not just the ones that have been updated by credit_formset.save)
				nick = nick_form.cleaned_data['nick'].commit()
				credits.update(nick=nick)

			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()

			new_credits = Credit.objects.filter(nick=nick, production=production)
			credits_description = ', '.join([credit.description for credit in new_credits])
			Edit.objects.create(action_type='edit_credit', focus=production,
				focus2=nick.releaser,
				description=(u"Updated %s's credit on %s: %s" % (nick, production, credits_description)),
				user=request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		nick_form = ProductionCreditedNickForm(nick=nick)
		credit_formset = CreditFormSet(queryset=credits, prefix="credit")
	return ajaxable_render(request, 'productions/edit_credit.html', {
		'html_title': "Editing credit for %s" % production.title,
		'production': production,
		'nick': nick,
		'nick_form': nick_form,
		'credit_formset': credit_formset,
	})


@login_required
def delete_credit(request, production_id, nick_id):
	production = get_object_or_404(Production, id=production_id)
	nick = get_object_or_404(Nick, id=nick_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			credits = Credit.objects.filter(nick=nick, production=production)
			if credits:
				credits.delete()
				production.updated_at = datetime.datetime.now()
				production.has_bonafide_edits = True
				production.save()
				Edit.objects.create(action_type='delete_credit', focus=production, focus2=nick.releaser,
					description=(u"Deleted %s's credit on %s" % (nick, production)), user=request.user)
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_credit', args=[production_id, nick_id]),
			"Are you sure you want to delete %s's credit from %s?" % (nick.name, production.title),
			html_title="Deleting %s's credit from %s" % (nick.name, production.title))


@login_required
def edit_soundtracks(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		formset = ProductionSoundtrackLinkFormset(request.POST, instance=production)
		if formset.is_valid():
			def form_order_key(form):
				if form.is_valid():
					return form.cleaned_data['ORDER'] or 9999
				else:
					return 9999

			sorted_forms = sorted(formset.forms, key=form_order_key)
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i + 1
			formset.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			for stl in production.soundtrack_links.all():
				stl.soundtrack.has_bonafide_edits = True
				stl.soundtrack.save()
			Edit.objects.create(action_type='edit_soundtracks', focus=production,
				description=(u"Edited soundtrack details for %s" % production.title), user=request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionSoundtrackLinkFormset(instance=production)
	return ajaxable_render(request, 'productions/edit_soundtracks.html', {
		'html_title': "Editing soundtrack details for %s" % production.title,
		'production': production,
		'formset': formset,
	})


@login_required
def add_tag(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		tag_name = request.POST.get('tag_name', '').strip()
		if tag_name:
			production.tags.add(tag_name)
			Edit.objects.create(action_type='production_add_tag', focus=production,
				description=u"Added tag '%s'" % tag_name, user=request.user)
	return HttpResponseRedirect(production.get_absolute_edit_url())


@login_required
def remove_tag(request, production_id, tag_id):
	production = get_object_or_404(Production, id=production_id)
	if request.method == 'POST':
		try:
			tag = production.tags.get(id=tag_id)
			production.tags.remove(tag)
			Edit.objects.create(action_type='production_remove_tag', focus=production,
				description=u"Removed tag '%s'" % tag.name, user=request.user)
		except Tag.DoesNotExist:
			pass
	return HttpResponseRedirect(production.get_absolute_edit_url())


def autocomplete(request):
	query = request.GET.get('term')
	productions = Production.objects.filter(title__istartswith=query)
	supertype = request.GET.get('supertype')
	if supertype:
		productions = productions.filter(supertype=supertype)
	productions = productions[:10]

	production_data = [
		{
			'id': production.id,
			'value': production.title,
			'title': production.title,
			'label': production.title_with_byline,
			'byline': production.byline_string,
			'supertype': production.supertype,
			'platform_name': production.platform_name,
			'production_type_name': production.type_name,
			'url': production.get_absolute_url(),
		}
		for production in productions
	]
	return HttpResponse(json.dumps(production_data), mimetype="text/javascript")


@login_required
def delete(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):
			# insert log entry before actually deleting, so that it doesn't try to
			# insert a null ID for the focus field
			Edit.objects.create(action_type='delete_production', focus=production,
				description=(u"Deleted production '%s'" % production.title), user=request.user)
			production.delete()
			messages.success(request, "'%s' deleted" % production.title)
			return HttpResponseRedirect(reverse('productions'))
		else:
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_production', args=[production_id]),
			"Are you sure you want to delete '%s'?" % production.title,
			html_title="Deleting %s" % production.title)
