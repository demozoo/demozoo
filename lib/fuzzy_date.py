import dateutil.parser
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
		date = dateutil.parser.parse(str, dayfirst = True).date()
		if YEAR_REGEX.match(str):
			return FuzzyDate(date, 'y')
		elif MONTH_REGEX.match(str):
			return FuzzyDate(date, 'm')
		else:
			return FuzzyDate(date, 'd')
