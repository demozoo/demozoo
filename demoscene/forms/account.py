from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from demoscene.models import AccountProfile


class AccountPreferencesForm(forms.ModelForm):
	class Meta:
		model = AccountProfile
		fields = ('sticky_edit_mode',)


class UserSignupForm(UserCreationForm):
	email = forms.EmailField(required=False, help_text=_('Needed if you want to be able to reset your password later on'))

	class Meta:
		fields = ('username', 'email')
		model = User
