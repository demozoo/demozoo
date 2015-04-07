from django import forms

from homepage.models import NewsStory, NewsImage

class NewsStoryForm(forms.ModelForm):
	class Meta:
		model = NewsStory
		fields = ['title', 'image', 'text', 'is_public']
		widgets = {
			'image': forms.HiddenInput()
		}


class NewsImageForm(forms.ModelForm):
	class Meta:
		model = NewsImage
		fields = ['image']
