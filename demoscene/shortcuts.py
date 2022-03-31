import datetime

from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from modal_workflow import render_modal_workflow

from demoscene.utils.ajax import request_is_ajax


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
            if kwargs.get('ajax_submit') and request_is_ajax(request):
                return HttpResponse('OK', content_type='text/plain')
            else:
                return HttpResponseRedirect(instance.get_absolute_url())
    else:
        form = form_class(instance=instance)

    title = kwargs.get('title')
    if title and title.endswith(':'):
        clean_title = title[:-1]
    else:
        clean_title = title

    return render(request, 'shared/simple_form.html', {
        'form': form,
        'html_form_class': kwargs.get('html_form_class'),
        'title': title,
        'html_title': clean_title,
        'action_url': reverse(url_name, args=[instance.id]),
        'ajax_submit': kwargs.get('ajax_submit'),
    })


def modal_workflow_confirmation(request, action_url, message, html_title=None):
    return render_modal_workflow(
        request,
        'shared/simple_confirmation.html', 'shared/simple_confirmation.js',
        {
            'html_title': html_title,
            'message': message,
            'action_url': action_url,
        }
    )
