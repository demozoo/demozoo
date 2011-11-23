from django import forms

class ExternalLinkForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(ExternalLinkForm, self).__init__(*args, **kwargs)
		self.fields['url'] = forms.CharField(label='URL', initial=self.instance.url)
	
	def save(self, commit = True):
		instance = super(ExternalLinkForm, self).save(commit = False)
		instance.url = self.cleaned_data['url']
		if commit:
			instance.save()
		return instance
	
	class Meta:
		fields = ['url']
