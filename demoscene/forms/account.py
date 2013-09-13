from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

from demoscene.models import AccountProfile


class AccountPreferencesForm(forms.ModelForm):
	class Meta:
		model = AccountProfile
		fields = ('sticky_edit_mode',)


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text=_('Needed if you think you\'ll forget your password'))

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit)
        user.email = self.cleaned_data['email'] if self.cleaned_data['email'] else ''
        if commit:
            user.save()
        return user
