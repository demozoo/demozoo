from django.test import TestCase

from common.utils.fuzzy_date import FuzzyDate
from demoscene.templatetags.demoscene_tags import date_range


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
