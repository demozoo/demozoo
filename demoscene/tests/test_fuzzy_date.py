from __future__ import absolute_import, unicode_literals

import datetime

from django import forms
from django.test import TestCase
from freezegun import freeze_time
from fuzzy_date import FuzzyDate
from fuzzy_date_field import FuzzyDateField


class TestFuzzyDate(TestCase):
    def test_invalid_precision(self):
        with self.assertRaises(KeyError):
            FuzzyDate(datetime.date(2020, 8, 1), 'x')

    def test_str(self):
        self.assertEqual(str(FuzzyDate(datetime.date(2020, 8, 1), 'd')).strip(), "1 August 2020")
        self.assertEqual(str(FuzzyDate(datetime.date(2020, 8, 1), 'm')), "August 2020")
        self.assertEqual(str(FuzzyDate(datetime.date(2020, 8, 1), 'y')), "2020")

    def test_short_format(self):
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'd').short_format(), "Aug 2020")
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'm').short_format(), "Aug 2020")
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'y').short_format(), "2020")

    def test_numeric_format(self):
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'd').numeric_format(), "2020-08-01")
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'm').numeric_format(), "2020-08")
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 1), 'y').numeric_format(), "2020")

    def test_date_range_start(self):
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'd').date_range_start(), datetime.date(2020, 8, 15))
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'm').date_range_start(), datetime.date(2020, 8, 1))
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'y').date_range_start(), datetime.date(2020, 1, 1))

    def test_date_range_end(self):
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'd').date_range_end(), datetime.date(2020, 8, 15))
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'm').date_range_end(), datetime.date(2020, 8, 31))
        self.assertEqual(FuzzyDate(datetime.date(2020, 8, 15), 'y').date_range_end(), datetime.date(2020, 12, 31))

    def test_agrees_with(self):
        d1 = FuzzyDate(datetime.date(2020, 8, 1), 'd')
        d2 = FuzzyDate(datetime.date(2020, 8, 1), 'd')
        d3 = FuzzyDate(datetime.date(2020, 8, 2), 'd')
        self.assertTrue(d1.agrees_with(None))
        self.assertTrue(d1.agrees_with(d2))
        self.assertFalse(d1.agrees_with(d3))

        m3 = FuzzyDate(datetime.date(2020, 8, 2), 'm')
        self.assertTrue(d1.agrees_with(m3))

        y1 = FuzzyDate(datetime.date(2020, 1, 1), 'y')
        self.assertTrue(y1.agrees_with(d1))

    def test_eq(self):
        d1 = FuzzyDate(datetime.date(2020, 8, 1), 'd')
        d2 = FuzzyDate(datetime.date(2020, 8, 1), 'd')
        m1 = FuzzyDate(datetime.date(2020, 8, 1), 'm')
        m2 = FuzzyDate(datetime.date(2020, 8, 2), 'm')
        y1 = FuzzyDate(datetime.date(2020, 8, 1), 'y')
        y2 = FuzzyDate(datetime.date(2020, 1, 2), 'y')

        self.assertTrue(d1 == d2)
        self.assertFalse(d1 == m1)
        self.assertTrue(m1 == m2)
        self.assertTrue(y1 == y2)

    @freeze_time('2020-08-31')
    def test_parse(self):
        self.assertEqual(str(FuzzyDate.parse('1993-02-07')).strip(), "7 February 1993")
        self.assertEqual(str(FuzzyDate.parse('7 Feb')).strip(), "7 February 2020")
        self.assertEqual(str(FuzzyDate.parse('02/07/1993')).strip(), "2 July 1993")


class FuzzyDateForm(forms.Form):
    date = FuzzyDateField()


class TestFuzzyDateField(TestCase):
    def test_valid(self):
        form = FuzzyDateForm({'date': '15 march 2000'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date'], FuzzyDate(datetime.date(2000, 3, 15), 'd'))

    def test_passing_fuzzy_date(self):
        form = FuzzyDateForm({'date': FuzzyDate(datetime.date(2000, 3, 15), 'd')})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date'], FuzzyDate(datetime.date(2000, 3, 15), 'd'))

    def test_fail_parsing(self):
        form = FuzzyDateForm({'date': '15 smarch 2000'})
        self.assertFalse(form.is_valid())

    def test_fail_parsing_2(self):
        # regression in python-dateutil 2.8.1:
        # https://github.com/dateutil/dateutil/issues/1071
        form = FuzzyDateForm({'date': '1991-93'})
        self.assertFalse(form.is_valid())

    def test_out_of_range(self):
        form = FuzzyDateForm({'date': '15 march 1850'})
        self.assertFalse(form.is_valid())
