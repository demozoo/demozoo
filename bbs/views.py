from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from bbs.forms import BBSEditNotesForm, BBSForm
from bbs.models import BBS
from demoscene.models import Edit
from demoscene.shortcuts import get_page, simple_ajax_confirmation, simple_ajax_form
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
    bbstros = bbs.bbstros.prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')

    return render(request, 'bbs/show.html', {
        'bbs': bbs,
        'bbstros': bbstros
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


@writeable_site_required
@login_required
def edit(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == 'POST':
        form = BBSForm(request.POST, instance=bbs)
        if form.is_valid():
            form.save()
            form.log_edit(request.user)

            messages.success(request, 'BBS updated')
            return redirect('bbs', bbs.id)
    else:
        form = BBSForm(instance=bbs)

    title = "Editing BBS: %s" % bbs.name
    return render(request, 'shared/simple_form.html', {
        'html_title': title,
        'title': title,
        'form': form,
        'action_url': reverse('edit_bbs', args=[bbs.id])
    })


@writeable_site_required
@login_required
def edit_notes(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    if not request.user.is_staff:
        return redirect('bbs', bbs.id)

    def success(form):
        form.log_edit(request.user)

    return simple_ajax_form(request, 'bbs_edit_notes', bbs, BBSEditNotesForm,
        title='Editing notes for %s' % bbs.name, on_success=success
    )


@writeable_site_required
@login_required
def delete(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    if not request.user.is_staff:
        return redirect('bbs', bbs.id)
    if request.method == 'POST':
        if request.POST.get('yes'):

            # insert log entry before actually deleting, so that it doesn't try to
            # insert a null ID for the focus field
            Edit.objects.create(action_type='delete_bbs', focus=bbs,
                description=(u"Deleted BBS '%s'" % bbs.name), user=request.user)

            bbs.delete()

            messages.success(request, "BBS '%s' deleted" % bbs.name)
            return redirect('bbses')
        else:
            return redirect('bbs', bbs.id)
    else:
        return simple_ajax_confirmation(request,
            reverse('delete_bbs', args=[bbs.id]),
            "Are you sure you want to delete %s?" % bbs.name,
            html_title="Deleting %s" % bbs.name)
