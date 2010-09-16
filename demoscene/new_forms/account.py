from django import forms
from demoscene.models import AccountProfile

class AccountPreferencesForm(forms.ModelForm):
	class Meta:
		model = AccountProfile
		fields = ('sticky_edit_mode',)