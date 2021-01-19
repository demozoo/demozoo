from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from bbs.forms import AffiliationForm, BBSEditNotesForm, BBSForm, BBStroFormset, OperatorForm
from bbs.models import Affiliation, BBS, Operator
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

    # order by -role to get Sysop before Co-sysop. Will need to come up with something less hacky if more roles are added :-)
    staff = bbs.staff.select_related('releaser').defer('releaser__notes').order_by('-role', 'releaser__name')

    affiliations = bbs.affiliations.select_related('group').defer('group__notes').order_by(
        Concat('role', Value('999')),  # sort role='' after the numbered ones. Ewww.
        'group__name'
    )

    return render(request, 'bbs/show.html', {
        'bbs': bbs,
        'bbstros': bbstros,
        'staff': staff,
        'editing_staff': (request.GET.get('editing') == 'staff'),
        'affiliations': affiliations,
        'editing_affiliations': (request.GET.get('editing') == 'affiliations'),
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


@writeable_site_required
@login_required
def edit_bbstros(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    initial_forms = [
        {'production': production}
        for production in bbs.bbstros.all()
    ]

    if request.method == 'POST':
        formset = BBStroFormset(request.POST, initial=initial_forms)
        if formset.is_valid():
            bbstros = [prod_form.cleaned_data['production'].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms
                    and 'production' in prod_form.cleaned_data
            ]
            bbs.bbstros.set(bbstros)

            if formset.has_changed():
                bbstro_titles = [prod.title for prod in bbstros] or ['none']
                bbstro_titles = ", ".join(bbstro_titles)
                Edit.objects.create(action_type='edit_bbs_bbstros', focus=bbs,
                    description=u"Set BBStros to %s" % bbstro_titles, user=request.user)

            return redirect('bbs', bbs.id)
    else:
        formset = BBStroFormset(initial=initial_forms)
    return render(request, 'bbs/edit_bbstros.html', {
        'bbs': bbs,
        'formset': formset,
    })


def history(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    return render(request, 'bbs/history.html', {
        'bbs': bbs,
        'edits': Edit.for_model(bbs, request.user.is_staff),
    })


@writeable_site_required
@login_required
def add_operator(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == 'POST':
        form = OperatorForm(request.POST)
        if form.is_valid():
            releaser = form.cleaned_data['releaser_nick'].commit().releaser
            operator = Operator(
                releaser=releaser,
                bbs=bbs,
                role=form.cleaned_data['role'])
            operator.save()
            description = u"Added %s as staff member of %s" % (releaser.name, bbs.name)
            Edit.objects.create(action_type='add_bbs_operator', focus=releaser, focus2=bbs,
                description=description, user=request.user)
            return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=staff")
    else:
        form = OperatorForm()
    return render(request, 'bbs/add_operator.html', {
        'bbs': bbs,
        'form': form,
    })


@writeable_site_required
@login_required
def edit_operator(request, bbs_id, operator_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    operator = get_object_or_404(Operator, bbs=bbs, id=operator_id)

    if request.method == 'POST':
        form = OperatorForm(request.POST, initial={
            'releaser_nick': operator.releaser.primary_nick,
            'role': operator.role,
        })
        if form.is_valid():
            releaser = form.cleaned_data['releaser_nick'].commit().releaser
            operator.releaser = releaser
            operator.role = form.cleaned_data['role']
            operator.save()
            form.log_edit(request.user, releaser, bbs)

            return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=staff")
    else:
        form = OperatorForm(initial={
            'releaser_nick': operator.releaser.primary_nick,
            'role': operator.role,
        })
    return render(request, 'bbs/edit_operator.html', {
        'bbs': bbs,
        'operator': operator,
        'form': form,
    })


@writeable_site_required
@login_required
def remove_operator(request, bbs_id, operator_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    operator = get_object_or_404(Operator, bbs=bbs, id=operator_id)

    if request.method == 'POST':
        if request.POST.get('yes'):
            operator.delete()
            description = u"Removed %s as staff member of %s" % (operator.releaser.name, bbs.name)
            Edit.objects.create(action_type='remove_bbs_operator', focus=operator.releaser, focus2=bbs,
                description=description, user=request.user)
        return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=staff")
    else:
        return simple_ajax_confirmation(request,
            reverse('bbs_remove_operator', args=[bbs_id, operator_id]),
            "Are you sure you want to remove %s as staff member of %s?" % (operator.releaser.name, bbs.name),
            html_title="Removing %s as staff member of %s" % (operator.releaser.name, bbs.name))


@writeable_site_required
@login_required
def add_affiliation(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)

    if request.method == 'POST':
        form = AffiliationForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data['group_nick'].commit().releaser
            affiliation = Affiliation(
                group=group,
                bbs=bbs,
                role=form.cleaned_data['role'])
            affiliation.save()
            if affiliation.role:
                description = u"Added BBS %s as %s for %s" % (bbs.name, affiliation.get_role_display(), group.name)
            else:
                description = u"Added affiliation with BBS %s for %s" % (bbs.name, group.name)
            Edit.objects.create(action_type='add_bbs_affiliation', focus=group, focus2=bbs,
                description=description, user=request.user)
            return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=affiliations")
    else:
        form = AffiliationForm()
    return render(request, 'bbs/add_affiliation.html', {
        'bbs': bbs,
        'form': form,
    })


@writeable_site_required
@login_required
def edit_affiliation(request, bbs_id, affiliation_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    affiliation = get_object_or_404(Affiliation, bbs=bbs, id=affiliation_id)

    if request.method == 'POST':
        form = AffiliationForm(request.POST, initial={
            'group_nick': affiliation.group.primary_nick,
            'role': affiliation.role,
        })
        if form.is_valid():
            group = form.cleaned_data['group_nick'].commit().releaser
            affiliation.group = group
            affiliation.role = form.cleaned_data['role']
            affiliation.save()
            form.log_edit(request.user, affiliation)

            return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=affiliations")
    else:
        form = AffiliationForm(initial={
            'group_nick': affiliation.group.primary_nick,
            'role': affiliation.role,
        })
    return render(request, 'bbs/edit_affiliation.html', {
        'bbs': bbs,
        'affiliation': affiliation,
        'form': form,
    })


@writeable_site_required
@login_required
def remove_affiliation(request, bbs_id, affiliation_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    affiliation = get_object_or_404(Affiliation, bbs=bbs, id=affiliation_id)

    if request.method == 'POST':
        if request.POST.get('yes'):
            affiliation.delete()
            description = u"Removed %s's affiliation with %s" % (affiliation.group.name, bbs.name)
            Edit.objects.create(action_type='remove_bbs_affiliation', focus=affiliation.group, focus2=bbs,
                description=description, user=request.user)
        return HttpResponseRedirect(bbs.get_absolute_edit_url() + "?editing=affiliations")
    else:
        return simple_ajax_confirmation(request,
            reverse('bbs_remove_affiliation', args=[bbs_id, affiliation_id]),
            "Are you sure you want to remove %s's affiliation with %s?" % (affiliation.group.name, bbs.name),
            html_title="Removing %s's affiliation with %s" % (affiliation.group.name, bbs.name))
