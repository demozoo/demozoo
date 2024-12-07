from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from demoscene.models import Edit, Nick
from platforms.models import Platform

from ..fields.byline_field import BylineLookup
from ..fields.byline_search import BylineSearch
from ..fields.production_field import ProductionField, ProductionSelection
from ..forms import (
    PackMemberFormset,
    ProductionCreditedNickForm,
    ProductionDownloadLinkForm,
    ProductionEditCoreDetailsForm,
    ProductionExternalLinkForm,
    ProductionExternalLinkFormSet,
    ProductionIndexFilterForm,
    ProductionSoundtrackLinkFormset,
)
from ..models import Production, ProductionLink, ProductionType


class ProductionsFormsTests(TestCase):
    def test_productionindexfilterform_type(self):
        form = ProductionIndexFilterForm()
        self.assertEqual(form.fields['production_type'].queryset.count(),
                         ProductionType.featured_types().count())

    def test_external_links_formset_delete(self):
        production = Production.objects.create(title='State of the Art')
        link = production.links.create(is_download_link=False, link_class='BaseUrl', parameter='https://demozoo.org')
        data = {
            'links-0-id': link.pk, 'links-0-url': 'https://demozoo.org', 'links-0-DELETE': 'on',
            'links-TOTAL_FORMS': '3', 'links-INITIAL_FORMS': '1', 'links-MAX_NUM_FORMS': '1000',
        }
        formset = ProductionExternalLinkFormSet(data, instance=production,
                                                queryset=production.links.filter(is_download_link=False))
        self.assertTrue(formset.is_valid())
        formset.save_ignoring_uniqueness()
        self.assertEqual(production.links.filter(is_download_link=False).count(), 0)

    def test_save_external_link_form_with_commit(self):
        production = Production.objects.create(title='State of the Art')
        external_link = ProductionLink(production=production, is_download_link=False)
        form = ProductionExternalLinkForm({'url': 'https://demozoo.org'}, instance=external_link)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(production.links.filter(is_download_link=False).count(), 1)

    def test_save_download_link_form_with_commit(self):
        production = Production.objects.create(title='State of the Art')
        external_link = ProductionLink(production=production, is_download_link=True)
        form = ProductionDownloadLinkForm({'url': 'https://demozoo.org'}, instance=external_link)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(production.links.filter(is_download_link=True).count(), 1)

    def test_credited_nick_form(self):
        form = ProductionCreditedNickForm()
        self.assertTrue(form)

    def test_soundtrack_link_formset(self):
        formset = ProductionSoundtrackLinkFormset()
        self.assertTrue(formset)

    def test_pack_member_formset(self):
        formset = PackMemberFormset()
        self.assertTrue(formset)


class TestBylineLookup(TestCase):
    fixtures = ['tests/gasman.json']

    def test_repr(self):
        bl = BylineLookup.from_value(BylineSearch('Gasman/Hooy-Program'))
        self.assertEqual(repr(bl), '<BylineLookup: [NickSelection: 1, Gasman], [NickSelection: 5, Hooy-Program]>')

    def test_eq(self):
        bl = BylineLookup.from_value(BylineSearch('Gasman/Hooy-Program'))
        self.assertFalse(bl == 'fish')

    def test_from_value(self):
        with self.assertRaises(ValidationError):
            BylineLookup.from_value('fish')


class TestProductionSelection(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        ps = ProductionSelection(id=4, title="Pondlife")
        self.assertEqual(str(ps), 'ProductionSelection: 4 - Pondlife')

    def test_from_value(self):
        with self.assertRaises(ValidationError):
            ProductionSelection.from_value('fish')


class TestProductionField(TestCase):
    fixtures = ['tests/gasman.json']

    def test_render_without_byline(self):

        class ProdForm(forms.Form):
            production = ProductionField()

        production = Production.objects.create(title='State of the Art')
        form = ProdForm(initial={'production': production})
        form_html = form.as_p()

        self.assertIn('<b>State of the Art</b>', form_html)

    def test_render_with_production_type_field(self):

        class ProdForm(forms.Form):
            production = ProductionField(show_production_type_field=True)

        form = ProdForm(initial={'production': Production.objects.get(title='Pondlife')})
        form_html = form.as_p()
        self.assertIn('<label for="id_production_type">Type:</label>', form_html)

    def test_submit_with_production_type(self):

        class ProdForm(forms.Form):
            production = ProductionField(show_production_type_field=True)

        intro = ProductionType.objects.get(name='1K Intro')

        form = ProdForm({
            'production_id': '', 'production_title': 'Froob',
            'production_byline_search': '',
            'production_type': intro.id
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['production'].types_to_set, [intro])

        form = ProdForm({
            'production_id': '', 'production_title': 'Froob',
            'production_byline_search': '',
            'production_type': ''
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['production'].types_to_set, [])


class TestProductionCoreDetailsForm(TestCase):
    fixtures = ['tests/gasman.json']

    def test_log_edit(self):
        user = User.objects.create_user(username='testuser', password='12345')

        form = ProductionEditCoreDetailsForm({
            'title': 'P0ndlife',
            'byline_search': 'Hooy-Program',
            'byline_author_match_0_id': Nick.objects.get(name='Hooy-Program').id,
            'byline_author_match_0_name': 'Hooy-Program',
            'release_date': '18 March 2001',
            'types': [ProductionType.objects.get(name='Demo').id],
            'platforms': [Platform.objects.get(name='ZX Spectrum').id],
        }, instance=Production.objects.get(title='Pondlife'))
        self.assertTrue(form.is_valid())
        form.log_edit(user)

        edit = Edit.objects.get(user=user)
        self.assertIn("Set title to 'P0ndlife'", edit.description)
