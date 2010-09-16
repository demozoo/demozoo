from django import forms
import timelib, datetime
from django.core import validators
from django.core.exceptions import ValidationError

class AnyFormatDateField(forms.DateField):
	widget = forms.DateInput(format = '%e %b %Y', attrs={'class':'date'})
	def to_python(self, value):
		"""
		Validates that the input can be converted to a date. Returns a Python
		datetime.date object.
		"""
		if value in validators.EMPTY_VALUES:
			return None
		if isinstance(value, datetime.datetime):
			return value.date()
		if isinstance(value, datetime.date):
			return value
		try:
			return timelib.strtodatetime(value).date()
		except ValueError:
			raise ValidationError(self.error_messages['invalid'])
