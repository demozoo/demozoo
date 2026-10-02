from django import forms

from users.models import APIKey


class APIKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ["name"]
