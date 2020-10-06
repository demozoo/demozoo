from __future__ import absolute_import, unicode_literals

from fuzzy_date import FuzzyDate
from demoscene.templatetags.demoscene_tags import date_range

from django import forms, template
from django.test import TestCase


class TestDateRangeTag(TestCase):
    def test_unequal_precision(self):
        start_date = FuzzyDate.parse("1990")
        end_date = FuzzyDate.parse("july 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "? 1990 - ? July 1990")

        start_date = FuzzyDate.parse("july 1990")
        end_date = FuzzyDate.parse("1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "? July 1990 - ? 1990")

        start_date = FuzzyDate.parse("30 june 1990")
        end_date = FuzzyDate.parse("july 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "30 June 1990 - ? July 1990")

    def test_year_precision(self):
        start_date = FuzzyDate.parse("1990")
        end_date = FuzzyDate.parse("1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "1990")

        start_date = FuzzyDate.parse("1990")
        end_date = FuzzyDate.parse("1991")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "1990 - 1991")

    def test_month_precision(self):
        start_date = FuzzyDate.parse("june 1990")
        end_date = FuzzyDate.parse("june 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "June 1990")

        start_date = FuzzyDate.parse("june 1990")
        end_date = FuzzyDate.parse("july 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "June - July 1990")

        start_date = FuzzyDate.parse("december 1990")
        end_date = FuzzyDate.parse("january 1991")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "December 1990 - January 1991")

        start_date = FuzzyDate.parse("june 1990")
        end_date = FuzzyDate.parse("june 1991")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "June 1990 - June 1991")

    def test_day_precision(self):
        start_date = FuzzyDate.parse("15 june 1990")
        end_date = FuzzyDate.parse("15 june 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "15th June 1990")

        start_date = FuzzyDate.parse("15 june 1990")
        end_date = FuzzyDate.parse("17 june 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "15th - 17th June 1990")

        start_date = FuzzyDate.parse("30 june 1990")
        end_date = FuzzyDate.parse("2 july 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "30th June - 2nd July 1990")

        start_date = FuzzyDate.parse("1 june 1990")
        end_date = FuzzyDate.parse("1 july 1990")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "1st June - 1st July 1990")

        start_date = FuzzyDate.parse("11 june 1990")
        end_date = FuzzyDate.parse("11 june 1991")
        result = date_range(start_date, end_date)
        self.assertEqual(result, "11th June 1990 - 11th June 1991")


class TestSpawningFormsetTag(TestCase):
    def test_spawningformset_without_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template('{% load spawning_formset %}{% spawningformset %}{% endspawningformset %}')

    def test_spawningformset_with_undefined_var(self):
        tpl = template.Template('{% load spawning_formset %}{% spawningformset foo %}{% endspawningformset %}')
        context = template.Context({})
        result = tpl.render(context)
        self.assertEqual(result, '')

    def test_spawningform_without_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template('{% load spawning_formset %}{% spawningformset foo %}{% spawningform %}{% endspawningform %}{% endspawningformset %}')

    def test_spawningform_with_malformed_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template('{% load spawning_formset %}{% spawningformset foo %}{% spawningform bar %}{% endspawningform %}{% endspawningformset %}')

    def test_spawningformset_without_delete(self):
        class NameForm(forms.Form):
            name = forms.CharField()

        NameFormSet = forms.formset_factory(NameForm)
        formset = NameFormSet(initial=[{'name': "Raymond Luxury-Yacht"}])

        tpl = template.Template('{% load spawning_formset %}{% spawningformset formset %}{% spawningform as form %}{{ form.name }}{% endspawningform %}{% endspawningformset %}')
        context = template.Context({'formset': formset})
        result = tpl.render(context)

        self.assertIn('<div class="formset_item">', result)
        self.assertNotIn('<span class="delete">', result)
