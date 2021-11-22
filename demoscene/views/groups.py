import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from read_only_mode import writeable_site_required

from demoscene.forms.releaser import CreateGroupForm, GroupMembershipForm, GroupSubgroupForm
from demoscene.models import Edit, Membership, Nick, Releaser
from demoscene.shortcuts import get_page
from demoscene.views.generic import AjaxConfirmationView


def index(request):
    nick_page = get_page(
        Nick.objects.filter(releaser__is_group=True).extra(
            select={'lower_name': 'lower(demoscene_nick.name)'}
        ).order_by('lower_name'),
        request.GET.get('page', '1'))

    return render(request, 'groups/index.html', {
        'nick_page': nick_page,
    })


def show(request, group_id):
    group = get_object_or_404(Releaser, id=group_id)
    if not group.is_group:
        return HttpResponseRedirect(group.get_absolute_url())

    external_links = group.active_external_links.select_related('releaser').defer('releaser__notes')
    external_links = sorted(external_links, key=lambda obj: obj.sort_key)
    parties_organised = (
        group.parties_organised.select_related('party').defer('party__notes').order_by('-party__start_date_date')
    )
    bbs_affiliations = group.bbs_affiliations.select_related('bbs').defer('bbs__notes').order_by(
        Concat('role', Value('999')),  # sort role='' after the numbered ones. Ewww.
        'bbs__name'
    )

    return render(request, 'groups/show.html', {
        'group': group,
        'editing_nicks': (request.GET.get('editing') == 'nicks'),
        'supergroupships': (
            group.group_memberships.all().select_related('group').defer('group__notes')
            .order_by('-is_current', Lower('group__name'))
        ),
        'memberships': (
            group.member_memberships.filter(member__is_group=False).select_related('member')
            .defer('member__notes').order_by('-is_current', Lower('member__name'))
        ),
        'editing_members': (request.GET.get('editing') == 'members'),
        'editing_subgroups': (request.GET.get('editing') == 'subgroups'),
        'subgroupships': (
            group.member_memberships.filter(member__is_group=True).select_related('member')
            .defer('member__notes').order_by('-is_current', Lower('member__name'))
        ),
        'parties_organised': parties_organised,
        'bbs_affiliations': bbs_affiliations,
        'member_productions': (
            group.member_productions().prefetch_related(
                'author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types'
            ).defer(
                'notes', 'author_nicks__releaser__notes', 'author_affiliation_nicks__releaser__notes'
            ).order_by('-release_date_date', 'release_date_precision', '-sortable_title')
        ),
        'external_links': external_links,
        'prompt_to_edit': settings.SITE_IS_WRITEABLE and (request.user.is_staff or not group.locked),
        'show_locked_button': request.user.is_authenticated and group.locked,
        'show_lock_button': request.user.is_staff and settings.SITE_IS_WRITEABLE and not group.locked,
    })


def history(request, group_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)
    return render(request, 'groups/history.html', {
        'group': group,
        'edits': Edit.for_model(group, request.user.is_staff),
    })


@writeable_site_required
@login_required
def create(request):
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            form.log_creation(request.user)
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = CreateGroupForm()

    return render(request, 'shared/simple_form.html', {
        'form': form,
        'title': "New group",
        'html_title': "New group",
        'action_url': reverse('new_group'),
    })


@writeable_site_required
@login_required
def add_member(request, group_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)

    if not group.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = GroupMembershipForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data['scener_nick'].commit().releaser
            if not group.member_memberships.filter(member=member).count():
                membership = Membership(
                    member=member,
                    group=group,
                    is_current=form.cleaned_data['is_current'])
                membership.save()
                group.updated_at = datetime.datetime.now()
                group.save()
                description = u"Added %s as a member of %s" % (member.name, group.name)
                Edit.objects.create(
                    action_type='add_membership', focus=member, focus2=group,
                    description=description, user=request.user
                )
            return HttpResponseRedirect(group.get_absolute_url() + "?editing=members")
    else:
        form = GroupMembershipForm()
    return render(request, 'groups/add_member.html', {
        'group': group,
        'form': form,
    })


@writeable_site_required
@login_required
def remove_member(request, group_id, scener_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)
    scener = get_object_or_404(Releaser, is_group=False, id=scener_id)

    if not group.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        deletion_type = request.POST.get('deletion_type')
        if deletion_type == 'ex_member':
            # set membership to is_current=False - do not delete
            group.member_memberships.filter(member=scener).update(is_current=False)
            group.updated_at = datetime.datetime.now()
            group.save()
            Edit.objects.create(
                action_type='edit_membership', focus=scener, focus2=group,
                description=u"Updated %s's membership of %s: set as ex-member" % (scener.name, group.name),
                user=request.user
            )
            return HttpResponseRedirect(group.get_absolute_url() + "?editing=members")
        elif deletion_type == 'full':
            group.member_memberships.filter(member=scener).delete()
            group.updated_at = datetime.datetime.now()
            group.save()
            description = u"Removed %s as a member of %s" % (scener.name, group.name)
            Edit.objects.create(
                action_type='remove_membership', focus=scener, focus2=group,
                description=description, user=request.user
            )
            return HttpResponseRedirect(group.get_absolute_url() + "?editing=members")
        else:
            show_error_message = True

    else:
        show_error_message = False

    return render(request, 'groups/remove_member.html', {
        'group': group,
        'scener': scener,
        'show_error_message': show_error_message,
    })


@writeable_site_required
@login_required
def edit_membership(request, group_id, membership_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)
    membership = get_object_or_404(Membership, group=group, id=membership_id)

    if not group.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = GroupMembershipForm(request.POST, initial={
            'scener_nick': membership.member.primary_nick,
            'is_current': membership.is_current,
        })
        if form.is_valid():
            member = form.cleaned_data['scener_nick'].commit().releaser
            # skip saving if the value of the member (scener) field duplicates an existing one on this group
            if not group.member_memberships.exclude(id=membership_id).filter(member=member).count():
                membership.member = member
                membership.is_current = form.cleaned_data['is_current']
                membership.save()
                group.updated_at = datetime.datetime.now()
                group.save()
                form.log_edit(request.user, member, group)

            return HttpResponseRedirect(group.get_absolute_url() + "?editing=members")
    else:
        form = GroupMembershipForm(initial={
            'scener_nick': membership.member.primary_nick,
            'is_current': membership.is_current,
        })
    return render(request, 'groups/edit_membership.html', {
        'group': group,
        'membership': membership,
        'form': form,
    })


@writeable_site_required
@login_required
def add_subgroup(request, group_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)

    if not group.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = GroupSubgroupForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data['subgroup_nick'].commit().releaser
            if not group.member_memberships.filter(member=member).count():
                membership = Membership(
                    member=member,
                    group=group,
                    is_current=form.cleaned_data['is_current'])
                membership.save()
                group.updated_at = datetime.datetime.now()
                group.save()
                description = u"Added %s as a subgroup of %s" % (member.name, group.name)
                Edit.objects.create(
                    action_type='add_subgroup', focus=member, focus2=group,
                    description=description, user=request.user
                )
            return HttpResponseRedirect(group.get_absolute_url() + "?editing=subgroups")
    else:
        form = GroupSubgroupForm()
    return render(request, 'groups/add_subgroup.html', {
        'group': group,
        'form': form,
    })


class RemoveSubgroupView(AjaxConfirmationView):
    def get_object(self, request, group_id, subgroup_id):
        self.group = Releaser.objects.get(id=group_id, is_group=True)
        self.subgroup = Releaser.objects.get(id=subgroup_id, is_group=True)

    def is_permitted(self):
        return self.group.editable_by_user(self.request.user)

    def get_redirect_url(self):
        return self.group.get_absolute_url() + "?editing=subgroups"

    def get_action_url(self):
        return reverse('group_remove_subgroup', args=[self.group.id, self.subgroup.id])

    def get_message(self):
        return "Are you sure you want to remove %s as a subgroup of %s?" % (self.subgroup.name, self.group.name)

    def get_html_title(self):
        return "Removing %s from %s" % (self.subgroup.name, self.group.name)

    def perform_action(self):
        self.group.member_memberships.filter(member=self.subgroup).delete()
        self.group.updated_at = datetime.datetime.now()
        self.group.save()
        description = u"Removed %s as a subgroup of %s" % (self.subgroup.name, self.group.name)
        Edit.objects.create(
            action_type='remove_membership', focus=self.subgroup, focus2=self.group,
            description=description, user=self.request.user
        )


@writeable_site_required
@login_required
def edit_subgroup(request, group_id, membership_id):
    group = get_object_or_404(Releaser, is_group=True, id=group_id)
    membership = get_object_or_404(Membership, group=group, id=membership_id)

    if not group.editable_by_user(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = GroupSubgroupForm(request.POST, initial={
            'subgroup_nick': membership.member.primary_nick,
            'is_current': membership.is_current,
        })
        if form.is_valid():
            member = form.cleaned_data['subgroup_nick'].commit().releaser
            if not group.member_memberships.exclude(id=membership_id).filter(member=member).count():
                membership.member = member
                membership.is_current = form.cleaned_data['is_current']
                membership.save()
                group.updated_at = datetime.datetime.now()
                group.save()
                form.log_edit(request.user, member, group)
            return HttpResponseRedirect(group.get_absolute_url() + "?editing=subgroups")
    else:
        form = GroupSubgroupForm(initial={
            'subgroup_nick': membership.member.primary_nick,
            'is_current': membership.is_current,
        })
    return render(request, 'groups/edit_subgroup.html', {
        'group': group,
        'membership': membership,
        'form': form,
    })


class ConvertToScenerView(AjaxConfirmationView):
    action_url_path = 'group_convert_to_scener'
    html_title = "Converting %s to a scener"
    message = "Are you sure you want to convert %s into a scener?"

    def get_object(self, request, group_id):
        return Releaser.objects.get(id=group_id, is_group=True)

    def is_permitted(self):
        return self.request.user.is_staff and self.object.can_be_converted_to_scener()

    def perform_action(self):
        group = self.object

        group.is_group = False
        group.updated_at = datetime.datetime.now()
        group.save()
        for nick in group.nicks.all():
            # sceners do not have specific 'abbreviation' fields on their nicks
            if nick.abbreviation:
                nick.abbreviation = ''
                nick.save()

        Edit.objects.create(
            action_type='convert_to_scener', focus=group,
            description=(u"Converted %s from a group to a scener" % group), user=self.request.user
        )
