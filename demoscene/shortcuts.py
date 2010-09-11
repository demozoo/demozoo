from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from demoscene.models import AccountProfile

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
		form = form_class(request.POST, instance = instance)
		if form.is_valid():
			form.save()
		return HttpResponseRedirect(instance.get_absolute_edit_url())
	else:
		form = form_class(instance = instance)
	
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'html_form_class': kwargs.get('html_form_class'),
		'title': kwargs.get('title'),
		'action_url': reverse(url_name, args=[instance.id]),
	})

def simple_ajax_confirmation(request, action_url, message):
	return ajaxable_render(request, 'shared/simple_confirmation.html', {
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
