from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from demoscene.models import AccountProfile


class UserSignupForm(UserCreationForm):
	def __init__(self, *args, **kwargs):
		self.captcha_question = kwargs.pop('captcha')
		return super(UserSignupForm, self).__init__(*args, **kwargs)

	email = forms.EmailField(required=False, help_text=_('Needed if you want to be able to reset your password later on'))
	captcha = forms.CharField(required=True, label=_("To prove you're not a bot"),
		widget=forms.TextInput(attrs={'class': 'short'})
	)

	def clean_captcha(self):
		data = self.cleaned_data['captcha']
		if data.lower() != self.captcha_question.answer.lower():
			raise forms.ValidationError("Please adjust your humanity settings and try again.")
		return data

	class Meta:
		fields = ('username', 'email')
		model = User
