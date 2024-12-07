from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet, ModelFormOptions, inlineformset_factory

from common.fields import FuzzyDateField
from common.utils import groklinks
from demoscene.fields import NickField
from demoscene.forms.common import BaseExternalLinkFormSet, BaseTagsForm, ExternalLinkForm
from demoscene.models import Edit
from parties.fields import PartyField
from platforms.models import Platform
from productions.fields.byline_field import BylineField
from productions.fields.production_field import ProductionField
from productions.fields.production_type_field import ProductionTypeChoiceField, ProductionTypeMultipleChoiceField
from productions.models import (
    InfoFile,
    PackMember,
    Production,
    ProductionBlurb,
    ProductionLink,
    ProductionType,
    SoundtrackLink,
)


def readable_list(list):
    if len(list) == 0:
        return "none"
    else:
        return ", ".join([str(item) for item in list])


class BaseProductionEditCoreDetailsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", Production())
        super().__init__(*args, **kwargs)
        self.fields["title"] = forms.CharField(initial=self.instance.title, max_length=255)
        self.fields["byline"] = BylineField(required=False, initial=self.instance.byline_search(), label="By")
        self.fields["release_date"] = FuzzyDateField(
            required=False,
            initial=self.instance.release_date,
            help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")',
        )
        self.fields["platforms"] = forms.ModelMultipleChoiceField(
            required=False,
            label="Platform",
            initial=[platform.id for platform in self.instance.platforms.all()],
            queryset=Platform.objects.all(),
        )

    def save(self, commit=True):
        self.instance.title = self.cleaned_data["title"]

        # will probably fail if commit = False...
        if self.cleaned_data["byline"]:
            self.cleaned_data["byline"].commit(self.instance)
        else:
            self.instance.author_nicks.clear()
            self.instance.author_affiliation_nicks.clear()
        self.instance.unparsed_byline = None

        self.instance.platforms.set(self.cleaned_data["platforms"])
        self.instance.release_date = self.cleaned_data["release_date"]
        if commit:
            self.instance.save()
        return self.instance

    @property
    def changed_data_description(self):
        descriptions = []
        changed_fields = self.changed_data
        if "title" in changed_fields:
            descriptions.append("title to '%s'" % self.cleaned_data["title"])
        if "byline" in changed_fields:
            descriptions.append("author to '%s'" % self.cleaned_data["byline"])
        if "release_date" in changed_fields:
            descriptions.append("release date to %s" % self.cleaned_data["release_date"])
        if "type" in changed_fields:
            descriptions.append("type to %s" % self.cleaned_data["type"])
        if "types" in changed_fields:
            if len(self.cleaned_data["types"]) > 1:
                descriptions.append("types to %s" % readable_list(self.cleaned_data["types"]))
            else:
                descriptions.append("type to %s" % readable_list(self.cleaned_data["types"]))
        if "platform" in changed_fields:  # pragma: no cover
            descriptions.append("platform to %s" % self.cleaned_data["platform"])
        if "platforms" in changed_fields:
            if len(self.cleaned_data["platforms"]) > 1:
                descriptions.append("platforms to %s" % readable_list(self.cleaned_data["platforms"]))
            else:
                descriptions.append("platform to %s" % readable_list(self.cleaned_data["platforms"]))
        if descriptions:
            return "Set %s" % (", ".join(descriptions))

    def log_edit(self, user):
        description = self.changed_data_description
        if description:
            Edit.objects.create(
                action_type="edit_production_core_details", focus=self.instance, description=description, user=user
            )


class ProductionEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
    # has multiple types
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["types"] = ProductionTypeMultipleChoiceField(
            required=False,
            label="Type",
            initial=[typ.id for typ in self.instance.types.all()],
            queryset=ProductionType.featured_types(),
        )

        self.has_multiple_types = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.instance.types.set(self.cleaned_data["types"])


class MusicEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_multiple_types = False

        try:
            initial_type = self.instance.types.all()[0].id
        except IndexError:
            initial_type = None

        self.fields["type"] = ProductionTypeChoiceField(queryset=ProductionType.music_types(), initial=initial_type)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cleaned_data["type"]:
            self.instance.types.set([self.cleaned_data["type"]])
        return self.instance


class GraphicsEditCoreDetailsForm(BaseProductionEditCoreDetailsForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_multiple_types = False

        try:
            initial_type = self.instance.types.all()[0].id
        except IndexError:
            initial_type = None

        self.fields["type"] = ProductionTypeChoiceField(queryset=ProductionType.graphic_types(), initial=initial_type)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cleaned_data["type"]:
            self.instance.types.set([self.cleaned_data["type"]])
        return self.instance


class CreateProductionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", Production())
        super().__init__(*args, **kwargs)
        self.fields["title"] = forms.CharField(max_length=255)
        self.fields["byline"] = BylineField(required=False, label="By")
        self.fields["release_date"] = FuzzyDateField(
            required=False, help_text='(As accurately as you know it - e.g. "1996", "Mar 2010")'
        )
        self.fields["types"] = ProductionTypeMultipleChoiceField(
            required=False, label="Type", queryset=ProductionType.featured_types()
        )
        self.fields["platforms"] = forms.ModelMultipleChoiceField(
            required=False, label="Platform", queryset=Platform.objects.all()
        )

    def save(self, commit=True):
        if not commit:  # pragma: no cover
            raise Exception("we don't support saving CreateProductionForm with commit = False. Sorry!")

        if not self.instance.supertype:
            self.instance.supertype = "production"
        self.instance.title = self.cleaned_data["title"]
        self.instance.release_date = self.cleaned_data["release_date"]
        self.instance.save()
        if self.cleaned_data["byline"]:
            self.cleaned_data["byline"].commit(self.instance)
        self.instance.types.set(self.cleaned_data["types"])
        self.instance.platforms.set(self.cleaned_data["platforms"])
        return self.instance

    def log_creation(self, user):
        Edit.objects.create(
            action_type="create_production",
            focus=self.instance,
            description=("Added production '%s'" % self.instance.title),
            user=user,
        )


class CreateMusicForm(CreateProductionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"] = ProductionTypeChoiceField(
            queryset=ProductionType.music_types(), initial=ProductionType.objects.get(internal_name="music")
        )
        self.fields["platform"] = forms.ModelChoiceField(
            required=False, queryset=Platform.objects.all(), empty_label="Any"
        )

    def save(self, *args, **kwargs):
        self.instance.supertype = "music"
        super().save(*args, **kwargs)

        if self.cleaned_data["type"]:
            self.instance.types.set([self.cleaned_data["type"]])
        if self.cleaned_data["platform"]:
            self.instance.platforms.set([self.cleaned_data["platform"]])
        return self.instance


class CreateGraphicsForm(CreateProductionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"] = ProductionTypeChoiceField(
            queryset=ProductionType.graphic_types(), initial=ProductionType.objects.get(internal_name="graphics")
        )
        self.fields["platform"] = forms.ModelChoiceField(
            required=False, queryset=Platform.objects.all(), empty_label="Any"
        )

    def save(self, *args, **kwargs):
        self.instance.supertype = "graphics"
        super().save(*args, **kwargs)

        if self.cleaned_data["type"]:
            self.instance.types.set([self.cleaned_data["type"]])
        if self.cleaned_data["platform"]:
            self.instance.platforms.set([self.cleaned_data["platform"]])
        return self.instance


class ProductionEditNotesForm(forms.ModelForm):
    def log_edit(self, user):
        Edit.objects.create(
            action_type="edit_production_notes", focus=self.instance, description="Edited notes", user=user
        )

    class Meta:
        model = Production
        fields = ["notes"]


class ProductionBlurbForm(forms.ModelForm):
    class Meta:
        model = ProductionBlurb
        exclude = ["production"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "short_notes"}),
        }


class ProductionTagsForm(BaseTagsForm):
    class Meta(BaseTagsForm.Meta):
        model = Production


class ProductionDownloadLinkForm(ExternalLinkForm):
    def save(self, commit=True):
        # populate the source field of new instances with 'manual' to indicate that they
        # were created by filling in this form rather than automated matching
        if self.instance.pk is None:
            self.instance.source = "manual"

        instance = super().save(commit=False)

        if instance.link_class in groklinks.PRODUCTION_EXTERNAL_LINK_TYPES:
            instance.is_download_link = False
        else:
            instance.is_download_link = True

        if commit:
            instance.validate_unique()
            instance.save()
        return instance

    class Meta:
        model = ProductionLink
        exclude = [
            "parameter",
            "link_class",
            "production",
            "is_download_link",
            "description",
            "demozoo0_id",
            "file_for_screenshot",
            "is_unresolved_for_screenshotting",
        ]


ProductionDownloadLinkFormSet = inlineformset_factory(
    Production, ProductionLink, form=ProductionDownloadLinkForm, formset=BaseExternalLinkFormSet, extra=2
)


class ProductionExternalLinkForm(ExternalLinkForm):
    def save(self, commit=True):
        # populate the source field of new instances with 'manual' to indicate that they
        # were created by filling in this form rather than automated matching
        if self.instance.pk is None:
            self.instance.source = "manual"

        instance = super().save(commit=False)

        if instance.link_class in groklinks.PRODUCTION_DOWNLOAD_LINK_TYPES:
            instance.is_download_link = True
        else:
            instance.is_download_link = False

        if commit:
            instance.validate_unique()
            instance.save()
        return instance

    class Meta:
        model = ProductionLink
        exclude = [
            "parameter",
            "link_class",
            "production",
            "is_download_link",
            "description",
            "demozoo0_id",
            "file_for_screenshot",
            "is_unresolved_for_screenshotting",
        ]


ProductionExternalLinkFormSet = inlineformset_factory(
    Production, ProductionLink, form=ProductionExternalLinkForm, formset=BaseExternalLinkFormSet
)


class ProductionCreditedNickForm(forms.Form):
    def __init__(self, *args, **kwargs):
        nick = kwargs.pop("nick", None)
        production = kwargs.pop("production", None)

        if production:
            # get the list of groups who made the production, and tell the NickField to
            # prioritise members of those groups
            authoring_groups = [
                group_nick.releaser for group_nick in production.author_nicks.filter(releaser__is_group=True)
            ]
        else:
            authoring_groups = []

        super().__init__(*args, **kwargs)
        if nick:
            self.fields["nick"] = NickField(initial=nick, prefer_members_of=authoring_groups)
        else:
            self.fields["nick"] = NickField(prefer_members_of=authoring_groups)


# An individual form row in the 'edit soundtrack details' form.
# Even though this corresponds to a SoundtrackLink object, this can't be a ModelForm
# because ModelForm internals would attempt to create an instance of SoundtrackLink
# immediately upon validation;
# - which we can't do because self.cleaned_data['soundtrack'] is a ProductionSelection,
# not a Production;
# - we can't use Production because that would require us to commit the production to
# the database immediately, which we may not want to do (e.g. if validation elsewhere fails)
# - and we can't use an unsaved Production object there because it has dependent relations.
class SoundtrackLinkForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", SoundtrackLink())
        super().__init__(*args, **kwargs)
        self.fields["soundtrack"] = ProductionField(
            initial=self.instance.soundtrack_id,
            supertype="music",
            types_to_set=[ProductionType.objects.get(internal_name="music")],
        )
        self._meta = ModelFormOptions()  # required by BaseModelFormSet.add_fields. eww.

    def save(self, commit=True):
        if not commit:  # pragma: no cover
            raise Exception("we don't support saving SoundtrackLinkForm with commit = False. Sorry!")

        self.instance.soundtrack = self.cleaned_data["soundtrack"].commit()
        self.instance.save()
        return self.instance

    def has_changed(self):
        return True  # force all objects to be saved so that ordering (done out of form) takes effect


# A base formset class dedicated to the 'edit soundtrack details' formset, which
# behaves mostly like a ModelFormSet but needs several methods of BaseModelFormSet
# to be monkeypatched to cope with SoundtrackLinkForm not being a true ModelForm
class BaseProductionSoundtrackLinkFormSet(BaseModelFormSet):
    def __init__(self, data=None, files=None, instance=None, prefix=None):
        self.model = SoundtrackLink
        if instance is None:
            self.instance = Production()
            qs = SoundtrackLink.objects.none()
        else:
            self.instance = instance
            qs = self.instance.soundtrack_links.order_by("position")
        super().__init__(data, files, prefix=prefix, queryset=qs)

    def validate_unique(self):
        # SoundtrackLinkForm has no unique constraints,
        # so don't try to rummage around in its non-existent metaclass to find some
        return

    def _construct_form(self, i, **kwargs):
        # ensure foreign key to production is set
        form = super()._construct_form(i, **kwargs)
        form.instance.production = self.instance
        return form


ProductionSoundtrackLinkFormset = formset_factory(
    SoundtrackLinkForm, formset=BaseProductionSoundtrackLinkFormSet, can_delete=True, can_order=True, extra=1
)
ProductionSoundtrackLinkFormset.fk = [f for f in SoundtrackLink._meta.fields if f.name == "production"][0]


class PackMemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", PackMember())
        super().__init__(*args, **kwargs)
        self.fields["member"] = ProductionField(
            initial=self.instance.member_id,
            # supertype='production',  # add this if we require pack members to be productions (not music or gfx)
        )
        self._meta = ModelFormOptions()  # required by BaseModelFormSet.add_fields. eww.

    def save(self, commit=True):
        if not commit:  # pragma: no cover
            raise Exception("we don't support saving PackMemberForm with commit = False. Sorry!")

        self.instance.member = self.cleaned_data["member"].commit()
        self.instance.save()
        return self.instance

    def has_changed(self):
        return True  # force all objects to be saved so that ordering (done out of form) takes effect


class BasePackMemberFormSet(BaseModelFormSet):
    def __init__(self, data=None, files=None, instance=None, prefix=None):
        self.model = PackMember
        if instance is None:
            self.instance = Production()
            qs = PackMember.objects.none()
        else:
            self.instance = instance
            qs = self.instance.pack_members.order_by("position")
        super().__init__(data, files, prefix=prefix, queryset=qs)

    def validate_unique(self):
        # PackMemberForm has no unique constraints,
        # so don't try to rummage around in its non-existent metaclass to find some
        return

    def _construct_form(self, i, **kwargs):
        # ensure foreign key to pack is set
        form = super()._construct_form(i, **kwargs)
        form.instance.pack = self.instance
        return form


PackMemberFormset = formset_factory(
    PackMemberForm, formset=BasePackMemberFormSet, can_delete=True, can_order=True, extra=1
)
PackMemberFormset.fk = [f for f in PackMember._meta.fields if f.name == "pack"][0]


class ProductionInvitationPartyForm(forms.Form):
    party = PartyField(required=False)


ProductionInvitationPartyFormset = formset_factory(ProductionInvitationPartyForm, can_delete=True, extra=1)


class ProductionIndexFilterForm(forms.Form):
    platform = forms.ModelChoiceField(required=False, queryset=Platform.objects.all(), empty_label="All platforms")
    production_type = ProductionTypeChoiceField(
        required=False, queryset=ProductionType.objects.none(), empty_label="All types"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["production_type"].queryset = ProductionType.featured_types()


class GraphicsIndexFilterForm(forms.Form):
    platform = forms.ModelChoiceField(required=False, queryset=Platform.objects.all(), empty_label="All platforms")
    production_type = ProductionTypeChoiceField(
        required=False, queryset=ProductionType.objects.none(), empty_label="All types"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["production_type"].queryset = ProductionType.graphic_types()


class MusicIndexFilterForm(forms.Form):
    platform = forms.ModelChoiceField(required=False, queryset=Platform.objects.all(), empty_label="All platforms")
    production_type = ProductionTypeChoiceField(
        required=False, queryset=ProductionType.objects.none(), empty_label="All types"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["production_type"].queryset = ProductionType.music_types()


ProductionInfoFileFormset = inlineformset_factory(Production, InfoFile, fields=[], extra=0)
