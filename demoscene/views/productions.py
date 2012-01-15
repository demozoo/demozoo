from demoscene.shortcuts import *
from demoscene.models import Production, Byline, Releaser, Credit, Screenshot, ProductionType, ProductionLink
from demoscene.forms.production import *
from taggit.models import Tag
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import ValidationError
import datetime
try:
	import json
except ImportError:
	import simplejson as json

def index(request, supertype):
	queryset = Production.objects.filter(supertype = supertype)

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
	else: # supertype == 'music'
		title = "Music"
		add_item_url = reverse('new_music')
		add_item_text = "New music"
		menu_section = "music"

	queryset = apply_order(queryset, order)

	production_page = get_page(
		queryset,
		request.GET.get('page', '1') )
	
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
		tag = Tag.objects.get(slug = tag_slug)
	except Tag.DoesNotExist:
		tag = Tag(name = tag_slug)
	queryset = Production.objects.filter(supertype = supertype, tags__slug = tag_slug)
	
	order = request.GET.get('order', 'title')

	if supertype == 'production':
		title = "Productions tagged '%s'" % tag.name
	elif supertype == 'graphics':
		title = "Graphics tagged '%s'" % tag.name
	else: # supertype == 'music'
		title = "Music tagged '%s'" % tag.name
	
	queryset = apply_order(queryset, order)

	production_page = get_page(
		queryset,
		request.GET.get('page', '1') )
	
	return render(request, 'productions/index.html', {
		'title': title,
		'production_page': production_page,
		'order': order,
	})

def apply_order(queryset, order):
	if order == 'date':
		return queryset.order_by('release_date_date')
	else: # title
		return queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title')

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'production':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name'),
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.links.filter(is_download_link=True),
		'external_links': production.links.filter(is_download_link=False),
		'soundtracks': [
			link.soundtrack for link in
			production.soundtrack_links.order_by('position').select_related('soundtrack')
		],
		'competition_placings': production.competition_placings.order_by('competition__party__start_date_date'),
		'tags': production.tags.all(),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})
	

@login_required
def edit(request, production_id):
	set_edit_mode_active(True, request.user)
	return show(request, production_id, edit_mode = True)

def edit_done(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(production.get_absolute_url())
	
@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	
	if production.supertype == 'production':
		form_class = ProductionEditCoreDetailsForm
	elif production.supertype == 'graphics':
		form_class = GraphicsEditCoreDetailsForm
	else: # production.supertype == 'music':
		form_class = MusicEditCoreDetailsForm
	
	if request.method == 'POST':
		form = form_class(request.POST, instance = production)
		
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = form_class(instance = production)
	
	return ajaxable_render(request, 'productions/edit_core_details.html', {
		'html_title': "Editing %s: %s" % (production.supertype, production.title),
		'production': production,
		'form': form,
	})

@login_required
def edit_notes(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
		title = 'Editing notes for %s:' % production.title,
		update_datestamp = True, update_bonafide_flag = True)

@login_required
def edit_external_links(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	
	if request.method == 'POST':
		formset = ProductionExternalLinkFormSet(request.POST, instance = production, queryset=production.links.filter(is_download_link=False))
		if formset.is_valid():
			formset.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionExternalLinkFormSet(instance = production, queryset=production.links.filter(is_download_link=False))
	return ajaxable_render(request, 'productions/edit_external_links.html', {
		'html_title': "Editing external links for %s" % production.title,
		'production': production,
		'formset': formset,
	})

@login_required
def add_download_link(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	production_link = ProductionLink(production = production, is_download_link=True)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = production_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = production_link)
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Adding download link for %s:" % production.title,
		'html_title': "Adding download link for %s" % production.title,
		'action_url': reverse('production_add_download_link', args=[production.id]),
	})

@login_required
def edit_download_link(request, production_id, production_link_id):
	production = get_object_or_404(Production, id = production_id)
	production_link = get_object_or_404(ProductionLink, id=production_link_id, production=production, is_download_link=True)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = production_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = production_link)
	return ajaxable_render(request, 'productions/edit_download_link.html', {
		'html_title': "Editing download link for %s" % production.title,
		'form': form,
		'production': production,
		'production_link': production_link,
	})

@login_required
def delete_download_link(request, production_id, production_link_id):
	production = get_object_or_404(Production, id = production_id)
	production_link = get_object_or_404(ProductionLink, id = production_link_id, production = production, is_download_link=True)
	if request.method == 'POST':
		if request.POST.get('yes'):
			production_link.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_download_link', args = [production_id, production_link_id]),
			"Are you sure you want to delete this download link for %s?" % production.title,
			html_title = "Deleting download link for %s" % production.title )

@login_required
def screenshots(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/screenshots.html', {
		'production': production,
		'screenshots': production.screenshots.order_by('id'),
	})

@login_required
def add_screenshot(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		from django.forms import ImageField # use a standalone ImageField for validation
		image_field = ImageField()
		uploaded_files = request.FILES.getlist('screenshot')
		failed_filenames = []
		for file in uploaded_files:
			try:
				image_field.to_python(file)
				screenshot = Screenshot(original = file)
				#if screenshot.original:
				screenshot.production = production
				screenshot.save()
			except ValidationError:
				failed_filenames.append(file.name)
		if len(uploaded_files) > len(failed_filenames):
			# at least one screenshot was successfully added
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		if failed_filenames:
			if len(uploaded_files) == 1:
				messages.error(request, "The screenshot could not be added (file was corrupted, or not a valid image format)")
			elif len(uploaded_files) == len(failed_filenames):
				messages.error(request, "None of the screenshots could be added (files were corrupted, or not a valid image format)")
			elif len(failed_filenames) == 1:
				messages.error(request, "The screenshot %s could not be added (file was corrupted, or not a valid image format)" % failed_filenames[0])
			else:
				messages.error(request, "The following screenshots could not be added (files were corrupted, or not a valid image format): %s" % (', '.join(failed_filenames)))
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return ajaxable_render(request, 'productions/add_screenshot.html', {
		'html_title': "Adding screenshots for %s" % production.title,
		'production': production,
	})

@login_required
def delete_screenshot(request, production_id, screenshot_id):
	production = get_object_or_404(Production, id = production_id)
	screenshot = get_object_or_404(Screenshot, id = screenshot_id, production = production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			screenshot.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(reverse('production_screenshots', args=[production.id]))
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_screenshot', args = [production_id, screenshot_id]),
			"Are you sure you want to delete this screenshot for %s?" % production.title,
			html_title = "Deleting screenshot for %s" % production.title )

@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at = datetime.datetime.now())
		form = CreateProductionForm(request.POST, instance = production)
		download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance = production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateProductionForm(initial = {
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
	production = get_object_or_404(Production, id = production_id)
	credit = Credit(production = production)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/add_credit.html', {
		'html_title': "Adding credit for %s" % production.title,
		'production': production,
		'form': form,
	})

@login_required
def edit_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/edit_credit.html', {
		'html_title': "Editing credit for %s" % production.title,
		'production': production,
		'credit': credit,
		'form': form,
	})

@login_required
def delete_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			credit.delete()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_credit', args = [production_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, production.title),
			html_title = "Deleting %s's credit from %s" % (credit.nick.name, production.title) )

@login_required
def edit_soundtracks(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		formset = ProductionSoundtrackLinkFormset(request.POST, instance = production)
		if formset.is_valid():
			def form_order_key(form):
				if form.is_valid():
					return form.cleaned_data['ORDER'] or 9999
				else:
					return 9999
			
			sorted_forms = sorted(formset.forms, key = form_order_key)
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i+1
			formset.save()
			production.updated_at = datetime.datetime.now()
			production.has_bonafide_edits = True
			production.save()
			for stl in production.soundtrack_links.all():
				stl.soundtrack.has_bonafide_edits = True
				stl.soundtrack.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionSoundtrackLinkFormset(instance = production)
	return ajaxable_render(request, 'productions/edit_soundtracks.html', {
		'html_title': "Editing soundtrack details for %s" % production.title,
		'production': production,
		'formset': formset,
	})

@login_required
def add_tag(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		if request.POST.get('tag_name', '').strip():
			production.tags.add(request.POST.get('tag_name').strip())
	return HttpResponseRedirect(production.get_absolute_edit_url())

@login_required
def remove_tag(request, production_id, tag_name):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		production.tags.remove(tag_name)
	return HttpResponseRedirect(production.get_absolute_edit_url())

def autocomplete(request):
	query = request.GET.get('term')
	productions = Production.objects.filter(title__istartswith = query)
	supertype = request.GET.get('supertype')
	if supertype:
		productions = productions.filter(supertype = supertype)
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
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	if request.method == 'POST':
		if request.POST.get('yes'):
			production.delete()
			messages.success(request, "'%s' deleted" % production.title)
			return HttpResponseRedirect(reverse('productions'))
		else:
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_production', args = [production_id]),
			"Are you sure you want to delete %s?" % production.title,
			html_title = "Deleting %s" % production.title )
