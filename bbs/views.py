from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from read_only_mode import writeable_site_required
from taggit.models import Tag

from bbs.forms import (
    AffiliationForm, BBSEditNotesForm, BBSForm, BBSTagsForm, BBSTextAdFormset, BBStroFormset, OperatorForm
)
from bbs.models import BBS, Affiliation, Operator, TextAd
from demoscene.models import Edit
from demoscene.shortcuts import get_page, simple_ajax_form
from demoscene.views.generic import AddTagView, AjaxConfirmationView, EditTagsView, EditTextFilesView, RemoveTagView


def index(request):
    page = get_page(
        BBS.objects.order_by(Lower('name')),
        request.GET.get('page', '1')
    )

    return render(request, 'bbs/index.html', {
        'page': page,
    })


def tagged(request, tag_name):
    try:
        tag = Tag.objects.get(name=tag_name)
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
    queryset = BBS.objects.filter(tags__name=tag_name).order_by('name')

    page = get_page(queryset, request.GET.get('page', '1'))

    return render(request, 'bbs/tagged.html', {
        'tag': tag,
        'page': page,
    })


def show(request, bbs_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    bbstros = bbs.bbstros.order_by('-release_date_date', 'title').prefetch_related(
        'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types'
    )

    # order by -role to get Sysop before Co-sysop.
    # Will need to come up with something less hacky if more roles are added :-)
    staff = (
        bbs.staff.select_related('releaser').defer('releaser__notes')
        .order_by('-is_current', '-role', 'releaser__name')
    )

    affiliations = bbs.affiliations.select_related('group').defer('group__notes').order_by(
        Concat('role', Value('999')),  # sort role='' after the numbered ones. Ewww.
        'group__name'
    )

    if request.user.is_authenticated:
        tags_form = BBSTagsForm(instance=bbs)
    else:
        tags_form = None

    return render(request, 'bbs/show.html', {
        'bbs': bbs,
        'bbstros': bbstros,
        'staff': staff,
        'editing_staff': (request.GET.get('editing') == 'staff'),
        'affiliations': affiliations,
        'editing_affiliations': (request.GET.get('editing') == 'affiliations'),
        'text_ads': bbs.text_ads.all(),
        'tags': bbs.tags.order_by('name'),
        'tags_form': tags_form,
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

    return simple_ajax_form(
        request, 'bbs_edit_notes', bbs, BBSEditNotesForm,
        title='Editing notes for %s' % bbs.name, on_success=success
    )


class DeleteBBSView(AjaxConfirmationView):
    html_title = "Deleting %s"
    message = "Are you sure you want to delete %s?"
    action_url_path = 'delete_bbs'

    def get_object(self, request, bbs_id):
        return BBS.objects.get(id=bbs_id)

    def is_permitted(self):
        return self.request.user.is_staff

    def get_redirect_url(self):
        return reverse('bbses')

    def get_cancel_url(self):
        return self.object.get_absolute_url()

    def perform_action(self):
        # insert log entry before actually deleting, so that it doesn't try to
        # insert a null ID for the focus field
        Edit.objects.create(
            action_type='delete_bbs', focus=self.object,
            description=(u"Deleted BBS '%s'" % self.object.name), user=self.request.user
        )
        self.object.delete()
        messages.success(self.request, "'%s' deleted" % self.object.name)


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
            bbstros = [
                prod_form.cleaned_data['production'].commit()
                for prod_form in formset.forms
                if prod_form not in formset.deleted_forms and 'production' in prod_form.cleaned_data
            ]
            bbs.bbstros.set(bbstros)

            if formset.has_changed():
                bbstro_titles = [prod.title for prod in bbstros] or ['none']
                bbstro_titles = ", ".join(bbstro_titles)
                Edit.objects.create(
                    action_type='edit_bbs_bbstros', focus=bbs,
                    description=u"Set BBStros to %s" % bbstro_titles, user=request.user
                )

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
                role=form.cleaned_data['role'],
                is_current=form.cleaned_data['is_current']
            )
            operator.save()
            description = u"Added %s as staff member of %s" % (releaser.name, bbs.name)
            Edit.objects.create(
                action_type='add_bbs_operator', focus=releaser, focus2=bbs,
                description=description, user=request.user
            )
            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=staff")
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
            'is_current': operator.is_current,
        })
        if form.is_valid():
            releaser = form.cleaned_data['releaser_nick'].commit().releaser
            operator.releaser = releaser
            operator.role = form.cleaned_data['role']
            operator.is_current = form.cleaned_data['is_current']
            operator.save()
            form.log_edit(request.user, releaser, bbs)

            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=staff")
    else:
        form = OperatorForm(initial={
            'releaser_nick': operator.releaser.primary_nick,
            'role': operator.role,
            'is_current': operator.is_current,
        })
    return render(request, 'bbs/edit_operator.html', {
        'bbs': bbs,
        'operator': operator,
        'form': form,
    })


class RemoveOperatorView(AjaxConfirmationView):
    def get_object(self, request, bbs_id, operator_id):
        self.bbs = BBS.objects.get(id=bbs_id)
        self.operator = Operator.objects.get(bbs=self.bbs, id=operator_id)

    def get_redirect_url(self):
        return self.bbs.get_absolute_url() + "?editing=staff"

    def get_action_url(self):
        return reverse('bbs_remove_operator', args=[self.bbs.id, self.operator.id])

    def get_message(self):
        return "Are you sure you want to remove %s as staff member of %s?" % (
            self.operator.releaser.name, self.bbs.name
        )

    def get_html_title(self):
        return "Removing %s as staff member of %s" % (self.operator.releaser.name, self.bbs.name)

    def perform_action(self):
        self.operator.delete()
        description = u"Removed %s as staff member of %s" % (self.operator.releaser.name, self.bbs.name)
        Edit.objects.create(
            action_type='remove_bbs_operator', focus=self.operator.releaser, focus2=self.bbs,
            description=description, user=self.request.user
        )


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
            Edit.objects.create(
                action_type='add_bbs_affiliation', focus=group, focus2=bbs,
                description=description, user=request.user
            )
            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=affiliations")
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

            return HttpResponseRedirect(bbs.get_absolute_url() + "?editing=affiliations")
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


class RemoveAffiliationView(AjaxConfirmationView):
    def get_object(self, request, bbs_id, affiliation_id):
        self.bbs = BBS.objects.get(id=bbs_id)
        self.affiliation = Affiliation.objects.get(bbs=self.bbs, id=affiliation_id)

    def get_redirect_url(self):
        return self.bbs.get_absolute_url() + "?editing=affiliations"

    def get_action_url(self):
        return reverse('bbs_remove_affiliation', args=[self.bbs.id, self.affiliation.id])

    def get_message(self):
        return "Are you sure you want to remove %s's affiliation with %s?" % (
            self.affiliation.group.name, self.bbs.name
        )

    def get_html_title(self):
        return "Removing %s's affiliation with %s" % (self.affiliation.group.name, self.bbs.name)

    def perform_action(self):
        self.affiliation.delete()
        description = u"Removed %s's affiliation with %s" % (self.affiliation.group.name, self.bbs.name)
        Edit.objects.create(
            action_type='remove_bbs_affiliation', focus=self.affiliation.group, focus2=self.bbs,
            description=description, user=self.request.user
        )


class EditTextAdsView(EditTextFilesView):
    subject_model = BBS
    formset_class = BBSTextAdFormset
    relation_name = 'text_ads'
    upload_field_name = 'text_ad'
    template_name = 'bbs/edit_text_ads.html'
    subject_context_name = 'bbs'


@login_required
def text_ad(request, bbs_id, file_id):
    bbs = get_object_or_404(BBS, id=bbs_id)
    text_ad = get_object_or_404(TextAd, bbs=bbs, id=file_id)
    return render(request, 'bbs/show_text_ad.html', {
        'bbs': bbs,
        'text_ad': text_ad,
    })


class BBSEditTagsView(EditTagsView):
    subject_model = BBS
    form_class = BBSTagsForm
    action_type = 'bbs_edit_tags'


class BBSAddTagView(AddTagView):
    subject_model = BBS
    action_type = 'bbs_add_tag'
    template_name = 'bbs/_tags_list.html'


class BBSRemoveTagView(RemoveTagView):
    subject_model = BBS
    action_type = 'bbs_remove_tag'
    template_name = 'bbs/_tags_list.html'
