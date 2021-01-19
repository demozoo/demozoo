from django import forms
from django.forms.formsets import formset_factory

from form_with_location import ModelFormWithLocation
from nick_field import NickField

from bbs.models import AFFILIATION_TYPES, BBS, OPERATOR_TYPES
from demoscene.models import Edit
from productions.fields.production_field import ProductionField


class BBSForm(ModelFormWithLocation):
    def log_creation(self, user):
        Edit.objects.create(action_type='create_bbs', focus=self.instance,
            description=(u"Added BBS '%s'" % self.instance.name), user=user)

    @property
    def changed_data_description(self):
        descriptions = []
        changed_fields = self.changed_data
        if 'name' in changed_fields:
            descriptions.append(u"name to '%s'" % self.cleaned_data['name'])
        if 'location' in changed_fields:
            descriptions.append(u"location to %s" % self.cleaned_data['location'])
        if descriptions:
            return u"Set %s" % (u", ".join(descriptions))

    def log_edit(self, user):
        description = self.changed_data_description
        if description:
            Edit.objects.create(action_type='edit_bbs', focus=self.instance,
                description=description, user=user)

    class Meta:
        model = BBS
        fields = ('name', 'location')


class BBSEditNotesForm(forms.ModelForm):
    def log_edit(self, user):
        Edit.objects.create(action_type='edit_bbs_notes', focus=self.instance,
            description="Edited notes", user=user)

    class Meta:
        model = BBS
        fields = ['notes']


class BBStroForm(forms.Form):
    production = ProductionField()

BBStroFormset = formset_factory(BBStroForm, can_delete=True, extra=1)


class OperatorForm(forms.Form):
    releaser_nick = NickField(label='Staff member', sceners_only=True)
    role = forms.ChoiceField(label='Role', choices=OPERATOR_TYPES)

    def log_edit(self, user, releaser, bbs):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'releaser_nick' in changed_fields:
            descriptions.append(u"changed staff member to %s" % releaser)
        if 'role' in changed_fields:
            descriptions.append("changed role to %s" % self.cleaned_data['role'])
        if descriptions:
            description_list = u", ".join(descriptions)
            Edit.objects.create(action_type='edit_bbs_operator', focus=releaser, focus2=bbs,
                description=u"Updated %s as staff member of %s: %s" % (releaser, bbs, description_list),
                user=user)


class AffiliationForm(forms.Form):
    group_nick = NickField(label='Group', groups_only=True)
    role = forms.ChoiceField(label='Role', choices=[('', '')] + AFFILIATION_TYPES, required=False)

    def log_edit(self, user, affiliation):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if 'group_nick' in changed_fields:
            descriptions.append(u"changed group to %s" % affiliation.group)
        if 'role' in changed_fields:
            descriptions.append("changed role to %s" % (affiliation.get_role_display() or 'None'))
        if descriptions:
            description_list = u", ".join(descriptions)
            Edit.objects.create(action_type='edit_bbs_affiliation',
                focus=affiliation.group, focus2=affiliation.bbs,
                description=u"Updated %s's affiliation with %s: %s" % (affiliation.group, affiliation.bbs, description_list),
                user=user)
