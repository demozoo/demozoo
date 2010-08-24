from demoscene.shortcuts import *
from demoscene.models import Releaser, Nick, NickVariant
from demoscene.forms import ScenerAddGroupForm, ScenerEditExternalLinksForm, ScenerEditLocationForm, CreateScenerForm

from django.contrib.auth.decorators import login_required

def index(request):
	
	nick_page = get_page(
		Nick.objects.filter(releaser__is_group = False).extra(
			select={'lower_name': 'lower(demoscene_nick.name)'}
		).order_by('lower_name'),
		request.GET.get('page', '1') )
	
	return render(request, 'sceners/index.html', {
		'nick_page': nick_page,
	})

def show(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	return render(request, 'sceners/show.html', {
		'scener': scener,
	})

@login_required
def edit(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	return render(request, 'sceners/show.html', {
		'scener': scener,
		'editing': True,
		'editing_as_admin': request.user.is_staff,
	})

@login_required
def edit_external_links(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(scener.get_absolute_edit_url())
		
	return simple_ajax_form(request, 'scener_edit_external_links', scener, ScenerEditExternalLinksForm, {
		'html_form_class': 'external_links_form',
	})

@login_required
def edit_external_links(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(scener.get_absolute_edit_url())
		
	return simple_ajax_form(request, 'scener_edit_external_links', scener, ScenerEditExternalLinksForm,
		title = 'Editing external links for %s' % scener.name,
		html_form_class = 'external_links_form')
		
@login_required
def edit_location(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	
	return simple_ajax_form(request, 'scener_edit_location', scener, ScenerEditLocationForm,
		title = 'Editing location for %s' % scener.name)

@login_required
def create(request):
	if request.method == 'POST':
		scener = Releaser(is_group = False)
		form = CreateScenerForm(request.POST, instance = scener)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		form = CreateScenerForm()
	
	if request.is_ajax():
		template = 'shared/simple_form.html'
	else:
		template = 'shared/simple_form_page.html'
	return render(request, template, {
		'form': form,
		'title': "New scener",
		'action_url': reverse('new_scener'),
	})

@login_required
def add_group(request, scener_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	if request.method == 'POST':
		form = ScenerAddGroupForm(request.POST)
		if form.is_valid():
			if form.cleaned_data['group_id'] == 'newgroup':
				group = Releaser(name = form.cleaned_data['group_name'], is_group = True)
				group.save()
			else:
				# TODO: test for blank group_id (as sent by non-JS)
				group = Releaser.objects.get(id = form.cleaned_data['group_id'], is_group = True)
			scener.groups.add(group)
			return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		form = ScenerAddGroupForm()
	if request.is_ajax():
		template = 'sceners/add_group.html'
	else:
		template = 'sceners/add_group_page.html'
	return render(request, template, {
		'scener': scener,
		'form': form,
	})

@login_required
def remove_group(request, scener_id, group_id):
	scener = get_object_or_404(Releaser, is_group = False, id = scener_id)
	group = get_object_or_404(Releaser, is_group = True, id = group_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			scener.groups.remove(group)
		return HttpResponseRedirect(scener.get_absolute_edit_url())
	else:
		if request.is_ajax():
			template = 'sceners/remove_group.html'
		else:
			template = 'sceners/remove_group_page.html'
		return render(request, template, {
			'scener': scener,
			'group': group,
		})

def autocomplete(request):
	query = request.GET.get('q')
	new_option = request.GET.get('new_option', False)
	
	nick_variants = NickVariant.autocompletion_search(query,
		limit = request.GET.get('limit', 10),
		exact = request.GET.get('exact', False),
		sceners_only = True,
		groups = request.GET.getlist('group[]')
	)
	return render(request, 'sceners/autocomplete.txt', {
		'query': query,
		'nick_variants': nick_variants,
		'new_option': new_option,
	}, mimetype = 'text/plain')
