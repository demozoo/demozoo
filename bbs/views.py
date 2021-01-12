from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from bbs.forms import BBSForm
from bbs.models import BBS
from demoscene.shortcuts import get_page
from read_only_mode import writeable_site_required


def index(request):
    page = get_page(
        BBS.objects.order_by(Lower('name')),
        request.GET.get('page', '1')
    )

    return render(request, 'bbs/index.html', {
        'page': page,
    })


def show(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    return render(request, 'bbs/show.html', {
        'bbs': bbs,
    })


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        bbs = BBS()
        form = BBSForm(request.POST, instance=bbs)
        if form.is_valid():
            form.save()
            form.log_creation(request.user)

            if request.is_ajax():
                return HttpResponse('OK: %s' % bbs.get_absolute_url(), content_type='text/plain')
            else:
                messages.success(request, 'BBS added')
                return redirect('bbs', bbs.id)
    else:
        form = BBSForm()
    return render(request, 'shared/simple_form.html', {
        'form': form,
        'title': "New BBS",
        'html_title': "New bbs",
        'action_url': reverse('new_bbs'),
    })
