from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

import datetime

from demoscene.models import Releaser, Nick, ReleaserExternalLink, Edit
from form_with_location import ModelFormWithLocation
from nick_field import NickField
from demoscene.forms.common import ExternalLinkForm, BaseExternalLinkFormSet
from django.forms.models import inlineformset_factory


class CreateGroupForm(forms.ModelForm):
    abbreviation = forms.CharField(required=False, max_length=255,
        help_text="(optional - only if there's one that's actively being used. Don't just make one up!)"
    )
    nick_variant_list = forms.CharField(
        label="Other spellings / abbreviations of this name",
        required=False, max_length=255,
        help_text="(as a comma-separated list)"
    )

    def __init__(self, *args, **kwargs):
        super(CreateGroupForm, self).__init__(*args, **kwargs)
        self.instance.is_group = True
        self.updated_at = datetime.datetime.now()

    def save(self, commit=True):
        if commit:
            with transaction.atomic():
                instance = super(CreateGroupForm, self).save(commit=True)
                primary_nick = instance.primary_nick
                primary_nick.abbreviation = self.cleaned_data['abbreviation']
                primary_nick.nick_variant_list = self.cleaned_data['nick_variant_list']
                primary_nick.save()
        else:
            instance = super(CreateGroupForm, self).save(commit=False)

        return instance

    def log_creation(self, user):
        Edit.objects.create(action_type='create_group', focus=self.instance,
            description=(u"Added group '%s'" % self.instance.name), user=user)

    class Meta:
        model = Releaser
        fields = ('name',)


class CreateScenerForm(forms.ModelForm):
    nick_variant_list = forms.CharField(
        label="Other spellings / abbreviations of this name",
        required=False, max_length=255,
        help_text="(as a comma-separated list)"
    )

    def __init__(self, *args, **kwargs):
        super(CreateScenerForm, self).__init__(*args, **kwargs)
        self.instance.is_group = False
        self.updated_at = datetime.datetime.now()

    def save(self, commit=True):
        if commit:
            with transaction.atomic():
                instance = super(CreateScenerForm, self).save(commit=True)
                primary_nick = instance.primary_nick
                primary_nick.nick_variant_list = self.cleaned_data['nick_variant_list']
                primary_nick.save()
        else:
            instance = super(CreateScenerForm, self).save(commit=False)

        return instance

    def log_creation(self, user):
        Edit.objects.create(action_type='create_scener', focus=self.instance,
            description=(u"Added scener '%s'" % self.instance.name), user=user)

    class Meta:
        model = Releaser
        fields = ('name',)


class ScenerEditLocationForm(ModelFormWithLocation):
    def log_edit(self, user):
        Edit.objects.create(action_type='edit_scener_location', focus=self.instance,
            description=(u"Set location to %s" % self.instance.location), user=user)

    class Meta:
        model = Releaser
        fields = ('location',)


class ScenerEditRealNameForm(forms.ModelForm):
    def log_edit(self, user):
        changed_fields = self.changed_data
        if 'first_name' in changed_fields or 'surname' in changed_fields:
            # Don't give the real name in the log description, as we might redact it
            Edit.objects.create(action_type='edit_scener_real_name', focus=self.instance,
                description="Set real name", user=user)

    class Meta:
        model = Releaser
        fields = ['first_name', 'surname', 'real_name_note']
        widgets = {
            'real_name_note': forms.Textarea(attrs={'class': 'short_notes'}),
        }


class ReleaserEditNotesForm(forms.ModelForm):
    def log_edit(self, user):
        Edit.objects.create(action_type='edit_releaser_notes', focus=self.instance,
            description="Edited notes", user=user)

    class Meta:
        model = Releaser
        fields = ['notes']


class NickForm(forms.ModelForm):
    nick_variant_list = forms.CharField(
        label="Other spellings / abbreviations of this name",
        required=False, max_length=255,
        help_text="(as a comma-separated list)"
    )

    def __init__(self, releaser, *args, **kwargs):
        for_admin = kwargs.pop('for_admin', False)

        super(NickForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.initial['nick_variant_list'] = instance.nick_variant_list
        else:
            instance = None

        # allow them to set this as the primary nick, unless they're editing the primary nick now
        if not (instance and instance.name == releaser.name):
            self.fields['override_primary_nick'] = forms.BooleanField(
                label="Use this as their preferred name, instead of '%s'" % releaser.name,
                required=False)

        if not for_admin:
            try:
                del self.fields['differentiator']
            except KeyError:
                pass

    # override validate_unique so that we include the releaser test in unique_together validation;
    # see http://stackoverflow.com/questions/2141030/djangos-modelform-unique-together-validation/3757871#3757871
    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.remove('releaser')  # allow checking against the missing attribute
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as e:
            # replace the standard model validation error message
            # ("Nick with this Releaser and Name already exists.")
            # with one more meaningful for this form
            e.error_dict['__all__'] = [u'This nick cannot be added, as it duplicates an existing one.']
            self._update_errors(e)

    def save(self, commit=True):
        instance = super(NickForm, self).save(commit=False)
        instance.nick_variant_list = self.cleaned_data['nick_variant_list']
        if commit:
            instance.save()
        return instance

    def log_creation(self, user):
        Edit.objects.create(action_type='add_nick', focus=self.instance.releaser,
            description=(u"Added nick '%s'" % self.instance.name), user=user)

    class Meta:
        model = Nick
        fields = ('name', 'abbreviation', 'differentiator')


class ScenerNickForm(NickForm):
    def log_edit(self, user):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'name' in changed_fields:
            descriptions.append(u"changed name to '%s'" % self.instance.name)
        if 'nick_variant_list' in changed_fields:
            descriptions.append(u"changed aliases to '%s'" % self.instance.nick_variant_list)
        if self.cleaned_data.get('override_primary_nick'):
            descriptions.append("set as primary nick")
        if descriptions:
            description_list = u"; ".join(descriptions)
            Edit.objects.create(action_type='edit_nick', focus=self.instance.releaser,
                description=u"Edited nick '%s': %s" % (self.instance.name, description_list),
                user=user)

    class Meta(NickForm.Meta):
        fields = ['name']


class GroupNickForm(NickForm):
    def log_edit(self, user):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'name' in changed_fields:
            descriptions.append(u"changed name to '%s'" % self.instance.name)
        if 'abbreviation' in changed_fields:
            descriptions.append(u"changed abbreviation to '%s'" % self.instance.abbreviation)
        if 'differentiator' in changed_fields:
            descriptions.append(u"changed differentiator to '%s'" % self.instance.differentiator)
        if 'nick_variant_list' in changed_fields:
            descriptions.append(u"changed aliases to '%s'" % self.instance.nick_variant_list)
        if self.cleaned_data.get('override_primary_nick'):
            descriptions.append("set as primary nick")
        if descriptions:
            description_list = u"; ".join(descriptions)
            Edit.objects.create(action_type='edit_nick', focus=self.instance.releaser,
                description=u"Edited nick '%s': %s" % (self.instance.name, description_list),
                user=user)

    class Meta(NickForm.Meta):
        fields = ['name', 'abbreviation', 'differentiator']


class ScenerMembershipForm(forms.Form):
    group_nick = NickField(groups_only=True, label='Group name')
    is_current = forms.BooleanField(required=False, label='Current member?', initial=True)

    def log_edit(self, user, member, group):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'group_nick' in changed_fields:
            descriptions.append(u"changed group to %s" % group)
        if 'is_current' in changed_fields:
            if self.cleaned_data['is_current']:
                descriptions.append("set as current member")
            else:
                descriptions.append("set as ex-member")
        if descriptions:
            description_list = u", ".join(descriptions)
            Edit.objects.create(action_type='edit_membership', focus=member, focus2=group,
                description=u"Updated %s's membership of %s: %s" % (member, group, description_list),
                user=user)


class GroupMembershipForm(forms.Form):
    scener_nick = NickField(sceners_only=True, label='Scener name')
    is_current = forms.BooleanField(required=False, label='Current member?', initial=True)

    def log_edit(self, user, member, group):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'scener_nick' in changed_fields:
            descriptions.append(u"changed member to %s" % member)
        if 'is_current' in changed_fields:
            if self.cleaned_data['is_current']:
                descriptions.append("set as current member")
            else:
                descriptions.append("set as ex-member")
        if descriptions:
            description_list = u", ".join(descriptions)
            Edit.objects.create(action_type='edit_membership', focus=member, focus2=group,
                description=u"Updated %s's membership of %s: %s" % (member, group, description_list),
                user=user)


class GroupSubgroupForm(forms.Form):
    subgroup_nick = NickField(groups_only=True, label='Subgroup name')
    is_current = forms.BooleanField(required=False, label='Current subgroup?', initial=True)

    def log_edit(self, user, member, group):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'subgroup_nick' in changed_fields:
            descriptions.append(u"changed subgroup to %s" % member)
        if 'is_current' in changed_fields:
            if self.cleaned_data['is_current']:
                descriptions.append("set as current subgroup")
            else:
                descriptions.append("set as ex-subgroup")
        if descriptions:
            description_list = u", ".join(descriptions)
            Edit.objects.create(action_type='edit_subgroup', focus=member, focus2=group,
                description=u"Updated %s's status as a subgroup of %s: %s" % (member, group, description_list),
                user=user)


class ReleaserCreditForm(forms.Form):
    def __init__(self, releaser, *args, **kwargs):
        super(ReleaserCreditForm, self).__init__(*args, **kwargs)
        self.fields['nick'] = forms.ModelChoiceField(
            label='Credited as',
            queryset=releaser.nicks.order_by('name'),
            initial=releaser.primary_nick.id
        )
        self.fields['production_name'] = forms.CharField(label='On production', widget=forms.TextInput(attrs={'class': 'production_autocomplete'}))
        self.fields['production_id'] = forms.CharField(widget=forms.HiddenInput)


class ReleaserExternalLinkForm(ExternalLinkForm):
    class Meta:
        model = ReleaserExternalLink
        exclude = ['parameter', 'link_class', 'releaser']

ReleaserExternalLinkFormSet = inlineformset_factory(Releaser, ReleaserExternalLink,
    form=ReleaserExternalLinkForm, formset=BaseExternalLinkFormSet)
