from demoscene.shortcuts import *
from demoscene.models import Production, Byline
from demoscene.forms.production import *


from django.contrib.auth.decorators import login_required
import datetime


def show(request, production_id, edit_mode=False):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'graphics':
		return HttpResponseRedirect(production.get_absolute_url())

	edit_mode = edit_mode or sticky_editing_active(request.user)

	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name', 'category'),
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.links.filter(is_download_link=True),
		'external_links': production.links.filter(is_download_link=False),
		'competition_placings': production.competition_placings.order_by('competition__party__start_date_date'),
		'tags': production.tags.all(),
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})


@login_required
def edit(request, production_id):
	set_edit_mode_active(True, request.user)
	return show(request, production_id, edit_mode=True)


def history(request, production_id):
	production = get_object_or_404(Production, id=production_id)
	if production.supertype != 'graphics':
		return HttpResponseRedirect(production.get_history_url())
	return render(request, 'productions/history.html', {
		'production': production,
		'edits': Edit.for_model(production),
	})


@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at=datetime.datetime.now())
		form = CreateGraphicsForm(request.POST, instance=production)
		download_link_formset = ProductionDownloadLinkFormSet(request.POST, instance=production)
		if form.is_valid() and download_link_formset.is_valid():
			form.save()
			download_link_formset.save()
			form.log_creation(request.user)
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateGraphicsForm(initial={
			'byline': Byline.from_releaser_id(request.GET.get('releaser_id'))
		})
		download_link_formset = ProductionDownloadLinkFormSet()
	return ajaxable_render(request, 'graphics/create.html', {
		'html_title': "New graphics",
		'form': form,
		'download_link_formset': download_link_formset,
	})
