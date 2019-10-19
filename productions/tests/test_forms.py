from __future__ import unicode_literals

from django.test import TestCase

from ..forms import ProductionIndexFilterForm, ProductionExternalLinkForm, ProductionExternalLinkFormSet
from ..models import ProductionType, Production, ProductionLink


class ProductionsFormsTests(TestCase):
    def test_productionindexfilterform_type(self):
        form = ProductionIndexFilterForm()
        self.assertEqual(form.fields['production_type'].queryset.count(),
                         ProductionType.featured_types().count())

    def test_external_links_formset_delete(self):
        production = Production.objects.create(title='State of the Art')
        l = production.links.create(is_download_link=False, link_class='BaseUrl', parameter='https://demozoo.org')
        data = {'links-0-id': l.pk, 'links-0-url': 'https://demozoo.org', 'links-0-DELETE': 'on',
                'links-TOTAL_FORMS': '3', 'links-INITIAL_FORMS': '1', 'links-MAX_NUM_FORMS': '1000'}
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
