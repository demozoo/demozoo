from django import forms
from fuzzy_date import FuzzyDate
from django.core import validators
from django.core.exceptions import ValidationError


class FuzzyDateInput(forms.DateInput):
	def _has_changed(self, initial, data):
		return initial != FuzzyDate.parse(data)


class FuzzyDateField(forms.Field):
	widget = FuzzyDateInput(format='%e %b %Y', attrs={'class': 'date'})

	def to_python(self, value):
		"""
		Validates that the input can be converted to a date. Returns a
		FuzzyDate object.
		"""
		if value in validators.EMPTY_VALUES:
			return None
		if isinstance(value, FuzzyDate):
			return value
		try:
			result = FuzzyDate.parse(value)
		except ValueError:
			raise ValidationError(self.error_messages['invalid'])

		if result.date.year < 1900:
			raise ValidationError(self.error_messages['invalid'])

		return result
