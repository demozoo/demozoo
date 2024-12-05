from django import forms
from django.test import TestCase

from common.fields import SubmitButtonField


class TestSubmitButtonField(TestCase):
    def test_val(self):
        class SubmittableForm(forms.Form):
            lookup = SubmitButtonField(button_text='Look up name')

        form = SubmittableForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['lookup'], False)

        form = SubmittableForm({'lookup': "Look up name"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['lookup'], True)

    def test_render(self):
        button = SubmitButtonField(button_text='Look up name')
        html = button.widget.render('lookup', None)
        self.assertIn("Look up name", html)
