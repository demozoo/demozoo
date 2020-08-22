from __future__ import absolute_import, unicode_literals

import datetime

from django.test import TestCase

from fuzzy_date import FuzzyDate

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
