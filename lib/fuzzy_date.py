import dateutil.parser
import datetime
import re

MONTHS = "(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)"
YEAR_REGEX = re.compile(r"^\s*\d{4}\s*$")
MONTH_REGEX = re.compile(r"^\s*(%s|%s\W+\d{4}|\d{4}\W+%s|\d{1,2}\W+\d{4}|\d{4}\W+\d{1,2})\s*$" % (MONTHS, MONTHS, MONTHS), re.I)

class FuzzyDate():
	def __init__(self, date, precision):
		self.date = date
		self.precision = precision
	
	def __str__(self):
		if self.precision == 'y':
			return self.date.strftime("%Y")
		elif self.precision == 'm':
			return self.date.strftime("%B %Y")
		else:
			return self.date.strftime("%e %B %Y")
	
	def __unicode__(self):
		return self.__str__()
	
	def short_format(self):
		if self.precision == 'y':
			return self.date.strftime("%Y")
		else:
			return self.date.strftime("%b %Y")
	
	@staticmethod
	def parse(str):
		this_year = datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
		# using this as the default ensures that it doesn't try to fill in day/month with the current one,
		# leading to much hilarity when entering 'February 1996' on the 30th of the month - while still
		# allowing 'February' as a valid synonym for February of this year
		date = dateutil.parser.parse(str, dayfirst = True, default = this_year).date()
		if YEAR_REGEX.match(str):
			return FuzzyDate(date, 'y')
		elif MONTH_REGEX.match(str):
			return FuzzyDate(date, 'm')
		else:
			return FuzzyDate(date, 'd')
