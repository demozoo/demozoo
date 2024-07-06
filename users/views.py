from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from demoscene.shortcuts import get_page
from demoscene.utils.pagination import PaginationControls


def index(request):
    if not request.user.is_staff:
        return redirect('home')

    users = User.objects.order_by('username')
    return render(request, 'users/index.html', {
        'users': users,
    })


def show(request, user_id):
    user = get_object_or_404(User, id=user_id)

    edits = user.edits.order_by('-timestamp').select_related('user', 'focus_content_type',
                                                             'focus2_content_type')
    if not request.user.is_staff:
        edits = edits.filter(admin_only=False)
    edits_page = get_page(
        edits,
        request.GET.get('page', '1'))

    return render(request, 'users/show.html', {
        'user': user,
        'edits_page': edits_page,
        'pagination_controls': PaginationControls(edits_page, reverse('user', args=[user_id])),
    })
