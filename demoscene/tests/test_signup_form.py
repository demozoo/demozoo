from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from demoscene.forms.account import UserSignupForm
from demoscene.models import CaptchaQuestion


class TestSignupForm(TestCase):
	def setUp(self):
		self.captcha = CaptchaQuestion.objects.create(
			question="How many legs do cows have?",
			answer="Four"
		)

	def test_valid_form(self):
		form = UserSignupForm({
			'username': 'bob',
			'email': '',
			'password1': 'swordfish',
			'password2': 'swordfish',
			'captcha': 'four',
		}, captcha=self.captcha)
		self.assertTrue(form.is_valid())

	def test_incorrect_captcha(self):
		form = UserSignupForm({
			'username': 'bob',
			'email': '',
			'password1': 'swordfish',
			'password2': 'swordfish',
			'captcha': 'eleven',
		}, captcha=self.captcha)
		self.assertFalse(form.is_valid())
