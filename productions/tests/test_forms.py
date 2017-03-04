from django.test import TestCase

from ..forms import ProductionIndexFilterForm
from ..models import ProductionType


class ProductionsFormsTests(TestCase):
    def test_productionindexfilterform_type(self):
        form = ProductionIndexFilterForm()
        self.assertEqual(form.fields['production_type'].queryset,
                         ProductionType.featured_types())
