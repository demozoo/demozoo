from django import forms
from django.forms.models import BaseInlineFormSet
from demoscene.models import Edit


class ExternalLinkForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(ExternalLinkForm, self).__init__(*args, **kwargs)
		self.fields['url'] = forms.CharField(label='URL', initial=self.instance.url)

	def save(self, commit=True):
		instance = super(ExternalLinkForm, self).save(commit=False)
		instance.url = self.cleaned_data['url']
		if commit:
			instance.save()
		return instance

	class Meta:
		fields = ['url']


class BaseExternalLinkFormSet(BaseInlineFormSet):
	def log_edit(self, user, action_type):
		descriptions = []

		if self.new_objects:
			added_urls = [link.url for link in self.new_objects]
			if len(added_urls) > 1:
				descriptions.append("Added links: %s" % ", ".join(added_urls))
			else:
				descriptions.append("Added link %s" % ", ".join(added_urls))

		if self.changed_objects:
			updated_urls = [link.url for (link, fields) in self.changed_objects]
			if len(updated_urls) > 1:
				descriptions.append("Updated links: %s" % ", ".join(updated_urls))
			else:
				descriptions.append("Updated link %s" % ", ".join(updated_urls))

		if self.deleted_objects:
			deleted_urls = [link.url for link in self.deleted_objects]
			if len(deleted_urls) > 1:
				descriptions.append("Deleted links: %s" % ", ".join(deleted_urls))
			else:
				descriptions.append("Deleted link %s" % ", ".join(deleted_urls))

		if descriptions:
			Edit.objects.create(action_type=action_type, focus=self.instance,
				description=("; ".join(descriptions)), user=user)
