from django.shortcuts import redirect, render
from django.urls import reverse

from bbs.models import BBS
from demoscene.models import Edit, Releaser
from demoscene.shortcuts import get_page
from demoscene.utils.pagination import PaginationControls
from productions.models import Production


def latest_activity(request):
    latest_added_sceners = Releaser.objects.filter(is_group=False).\
        prefetch_related('group_memberships__group__nicks').order_by('-created_at')[0:10]

    latest_updated_sceners = Releaser.objects.filter(is_group=False).\
        prefetch_related('group_memberships__group__nicks').order_by('-updated_at')[0:10]

    return render(request, 'latest_activity.html', {
        'latest_added_productions': Production.objects.order_by('-created_at')[0:10],
        'latest_updated_productions': Production.objects.order_by('-updated_at')[0:10],
        'latest_added_groups': Releaser.objects.filter(is_group=True).order_by('-created_at')[0:10],
        'latest_updated_groups': Releaser.objects.filter(is_group=True).order_by('-updated_at')[0:10],
        'latest_added_sceners': latest_added_sceners,
        'latest_updated_sceners': latest_updated_sceners,
        'latest_added_bbses': BBS.objects.order_by('-created_at')[0:10],
        'latest_updated_bbses': BBS.objects.order_by('-updated_at')[0:10],
    })


def error_test(request):
    if request.user.is_staff:
        raise Exception("This is a test of the emergency broadcast system.")
    else:
        return redirect('home')


def page_not_found_test(request):
    return render(request, '404.html')


def recent_edits(request):
    edits = Edit.objects.order_by('-timestamp').select_related('user')
    if not request.user.is_staff:
        edits = edits.filter(admin_only=False)
    edits_page = get_page(
        edits,
        request.GET.get('page', '1'))

    return render(request, 'recent_edits.html', {
        'edits_page': edits_page,
        'pagination_controls': PaginationControls(edits_page, reverse('recent_edits')),
    })
