import datetime

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory

from bbs.models import AFFILIATION_TYPES, BBS, OPERATOR_TYPES, BBSExternalLink, Name, TextAd
from common.forms import ModelFormWithLocation
from demoscene.fields import NickField
from demoscene.forms.common import BaseExternalLinkFormSet, BaseTagsForm, ExternalLinkForm
from demoscene.models import Edit
from productions.fields.production_field import ProductionField


class BBSForm(ModelFormWithLocation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.updated_at = datetime.datetime.now()

    def log_creation(self, user):
        Edit.objects.create(
            action_type="create_bbs",
            focus=self.instance,
            description=("Added BBS '%s'" % self.instance.name),
            user=user,
        )

    @property
    def changed_data_description(self):
        descriptions = []
        changed_fields = self.changed_data
        if "name" in changed_fields:
            descriptions.append("name to '%s'" % self.cleaned_data["name"])
        if "location" in changed_fields:
            descriptions.append("location to %s" % self.cleaned_data["location"])
        if descriptions:
            return "Set %s" % (", ".join(descriptions))

    class Meta:
        model = BBS
        fields = ("name", "location")


AlternativeNameFormSet = forms.inlineformset_factory(BBS, Name, fields=["name"], extra=1)


class BBSEditNotesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.updated_at = datetime.datetime.now()

    def log_edit(self, user):
        Edit.objects.create(action_type="edit_bbs_notes", focus=self.instance, description="Edited notes", user=user)

    class Meta:
        model = BBS
        fields = ["notes"]


class BBStroForm(forms.Form):
    production = ProductionField()


BBStroFormset = formset_factory(BBStroForm, can_delete=True, extra=1)


class OperatorForm(forms.Form):
    releaser_nick = NickField(label="Staff member", sceners_only=True)
    role = forms.ChoiceField(label="Role", choices=OPERATOR_TYPES)
    is_current = forms.BooleanField(required=False, label="Current member?", initial=True)

    def log_edit(self, user, releaser, bbs):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if "releaser_nick" in changed_fields:
            descriptions.append("changed staff member to %s" % releaser)
        if "is_current" in changed_fields:
            if self.cleaned_data["is_current"]:
                descriptions.append("set as current staff")
            else:
                descriptions.append("set as ex-staff")
        if "role" in changed_fields:
            descriptions.append("changed role to %s" % self.cleaned_data["role"])
        if descriptions:
            description_list = ", ".join(descriptions)
            Edit.objects.create(
                action_type="edit_bbs_operator",
                focus=releaser,
                focus2=bbs,
                description="Updated %s as staff member of %s: %s" % (releaser, bbs, description_list),
                user=user,
            )


class AffiliationForm(forms.Form):
    group_nick = NickField(label="Group", groups_only=True)
    role = forms.ChoiceField(label="Role", choices=[("", "")] + AFFILIATION_TYPES, required=False)

    def log_edit(self, user, affiliation):
        # build up log description
        descriptions = []
        changed_fields = self.changed_data
        if "group_nick" in changed_fields:
            descriptions.append("changed group to %s" % affiliation.group)
        if "role" in changed_fields:
            descriptions.append("changed role to %s" % (affiliation.get_role_display() or "None"))
        if descriptions:
            description_list = ", ".join(descriptions)
            Edit.objects.create(
                action_type="edit_bbs_affiliation",
                focus=affiliation.group,
                focus2=affiliation.bbs,
                description=(
                    "Updated %s's affiliation with %s: %s" % (affiliation.group, affiliation.bbs, description_list)
                ),
                user=user,
            )


BBSTextAdFormset = inlineformset_factory(BBS, TextAd, fields=[], extra=0)


class BBSTagsForm(BaseTagsForm):
    class Meta(BaseTagsForm.Meta):
        model = BBS


class BBSExternalLinkForm(ExternalLinkForm):
    class Meta:
        model = BBSExternalLink
        exclude = ["parameter", "link_class", "bbs"]


BBSExternalLinkFormSet = inlineformset_factory(
    BBS, BBSExternalLink, form=BBSExternalLinkForm, formset=BaseExternalLinkFormSet
)
