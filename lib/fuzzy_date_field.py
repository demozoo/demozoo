from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from fuzzy_date import FuzzyDate


class FuzzyDateField(forms.Field):
    widget = forms.DateInput(format='%e %b %Y', attrs={'class': 'date'})

    default_error_messages = {
        'invalid': _('Enter a valid date.'),
    }

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

    def has_changed(self, initial, data):
        return initial != FuzzyDate.parse(data)
