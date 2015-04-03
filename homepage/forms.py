from django import forms

from homepage.models import NewsStory

class NewsStoryForm(forms.ModelForm):
	class Meta:
		model = NewsStory
		fields = ['title', 'text']
