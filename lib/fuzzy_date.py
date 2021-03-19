from __future__ import absolute_import, unicode_literals

import calendar
import dateutil.parser
import datetime
import re

MONTHS = "(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)"
YEAR_REGEX = re.compile(r"^\s*\d{4}\s*$")
MONTH_REGEX = re.compile(r"^\s*(%s|%s\W+\d{4}|\d{4}\W+%s|\d{1,2}\W+\d{4}|\d{4}\W+\d{1,2})\s*$" % (MONTHS, MONTHS, MONTHS), re.I)


class FuzzyDate(object):
    def __init__(self, date, precision):
        self.date = date
        if precision == 'd' or precision == 'day':
            self.precision = 'd'
        elif precision == 'm' or precision == 'month':
            self.precision = 'm'
        elif precision == 'y' or precision == 'year':
            self.precision = 'y'
        else:
            raise KeyError('Unknown precision type: %s' % precision)

    def __str__(self):
        if self.precision == 'y':
            return self.date.strftime("%Y")
        elif self.precision == 'm':
            return self.date.strftime("%B %Y")
        else:
            return self.date.strftime("%e %B %Y")

    def short_format(self):
        if self.precision == 'y':
            return self.date.strftime("%Y")
        else:
            return self.date.strftime("%b %Y")

    def explicit_format(self):
        if self.precision == 'y':
            return self.date.strftime("? %Y")
        elif self.precision == 'm':
            return self.date.strftime("? %B %Y")
        else:
            return self.date.strftime("%e %B %Y")

    def numeric_format(self):
        if self.precision == 'y':
            return self.date.strftime("%Y")
        elif self.precision == 'm':
            return self.date.strftime("%Y-%m")
        else:
            return self.date.strftime("%Y-%m-%d")

    def date_range_start(self):
        if self.precision == 'y':
            return self.date.replace(month=1, day=1)
        elif self.precision == 'm':
            return self.date.replace(day=1)
        else:
            return self.date

    def date_range_end(self):
        if self.precision == 'y':
            return self.date.replace(month=12, day=31)
        elif self.precision == 'm':
            weekday, last_day = calendar.monthrange(self.date.year, self.date.month)
            return self.date.replace(day=last_day)
        else:
            return self.date

    # Returns true if the 'other' date matches this one
    # as far as the precision of the two dates go. Always
    # returns true for None, because None denotes a date which
    # is not known to any precision whatsoever
    def agrees_with(self, other):
        if other == None:
            return True
        elif self.precision == 'd' and other.precision == 'd':
            return (
                self.date.year == other.date.year
                and self.date.month == other.date.month
                and self.date.day == other.date.day)
        elif self.precision in ['d', 'm'] and other.precision in ['d', 'm']:
            return (
                self.date.year == other.date.year
                and self.date.month == other.date.month)
        else:
            return self.date.year == other.date.year

    def __eq__(self, other):
        if not isinstance(other, FuzzyDate):
            return False
        if self.precision != other.precision:
            return False
        if self.precision == 'd':
            return (self.date.year == other.date.year and self.date.month == other.date.month and self.date.day == other.date.day)
        elif self.precision == 'm':
            return (self.date.year == other.date.year and self.date.month == other.date.month)
        else:  # self.precision == 'y':
            return (self.date.year == other.date.year)

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def parse(str):
        if not str:
            return None
        this_year = datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        # using this as the default ensures that it doesn't try to fill in day/month with the current one,
        # leading to much hilarity when entering 'February 1996' on the 30th of the month - while still
        # allowing 'February' as a valid synonym for February of this year
        date = dateutil.parser.parse(str, dayfirst=True, default=this_year).date()
        if YEAR_REGEX.match(str):
            return FuzzyDate(date, 'y')
        elif MONTH_REGEX.match(str):
            return FuzzyDate(date, 'm')
        else:
            return FuzzyDate(date, 'd')
