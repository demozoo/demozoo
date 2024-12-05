from django import forms
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe


class SubmitButtonInput(forms.Widget):
    def __init__(self, attrs=None, button_text=None):
        super().__init__(attrs)
        self.button_text = button_text

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}

        final_attrs = self.build_attrs(self.attrs, dict(
            type='submit', name=name, value=self.button_text,
            **attrs
        ))
        return mark_safe(u'<input%s />' % flatatt(final_attrs))


class SubmitButtonField(forms.Field):
    widget = SubmitButtonInput

    def __init__(
        self, button_text=None, required=True, widget=None, label=None,
        initial=None, help_text=None, *args, **kwargs
    ):
        super().__init__(
            required=required, widget=widget, label=label,
            initial=initial, help_text=help_text, *args, **kwargs
        )
        self.widget.button_text = button_text

    def clean(self, value):
        return bool(value)

# example usage:
# class SubmittableForm(forms.Form):
#     lookup = SubmitButtonField(button_text = 'Look up name')
