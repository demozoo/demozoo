from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from demoscene.models import AccountProfile
import datetime


def render(request, template, context={}, **kwargs):
	return render_to_response(template, context, context_instance=RequestContext(request), **kwargs)


def ajaxable_render(request, template, context={}, **kwargs):
	if request.is_ajax():
		return render(request, template, context, **kwargs)
	else:
		context['subtemplate_name'] = template
		return render(request, "base_wrapper.html", context, **kwargs)


# TODO: see if we can (largely) replace this with get_absolute_url
def redirect(*args, **kwargs):
	return HttpResponseRedirect(reverse(*args, **kwargs))


def get_page(queryset, page_number, **kwargs):
	count = kwargs.get('count', 50)

	paginator = Paginator(queryset, count)

	# Make sure page request is an int. If not, deliver first page.
	try:
		page = int(page_number)
	except ValueError:
		page = 1

	# If page request (9999) is out of range, deliver last page of results.
	try:
		return paginator.page(page)
	except (EmptyPage, InvalidPage):
		return paginator.page(paginator.num_pages)


def simple_ajax_form(request, url_name, instance, form_class, **kwargs):
	if request.method == 'POST':
		form = form_class(request.POST, instance=instance)
		if form.is_valid():
			if kwargs.get('update_datestamp', False):
				instance.updated_at = datetime.datetime.now()
			if kwargs.get('update_bonafide_flag', False):
				instance.has_bonafide_edits = True
			form.save()
			if kwargs.get('on_success'):
				kwargs['on_success'](form)
			if kwargs.get('ajax_submit') and request.is_ajax():
				return HttpResponse('OK', mimetype='text/plain')
			else:
				return HttpResponseRedirect(instance.get_absolute_edit_url())
	else:
		form = form_class(instance=instance)

	title = kwargs.get('title')
	if title and title.endswith(':'):
		clean_title = title[:-1]
	else:
		clean_title = title

	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'html_form_class': kwargs.get('html_form_class'),
		'title': title,
		'html_title': clean_title,
		'action_url': reverse(url_name, args=[instance.id]),
		'ajax_submit': kwargs.get('ajax_submit'),
	})


def simple_ajax_confirmation(request, action_url, message, html_title=None):
	return ajaxable_render(request, 'shared/simple_confirmation.html', {
		'html_title': html_title,
		'message': message,
		'action_url': action_url,
	})


def sticky_editing_enabled(user):
	if not user.is_authenticated():
		return False
	try:
		profile = user.get_profile()
	except AccountProfile.DoesNotExist:
		return False
	return profile.sticky_edit_mode


def sticky_editing_active(user):
	return sticky_editing_enabled(user) and user.get_profile().edit_mode_active


def set_edit_mode_active(is_active, user):
	if sticky_editing_enabled(user):
		profile = user.get_profile()
		profile.edit_mode_active = is_active
		profile.save()
