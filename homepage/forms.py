from django import forms

from homepage.models import NewsStory, NewsImage, Banner, BannerImage


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


class BannerForm(forms.ModelForm):
	class Meta:
		model = Banner
		fields = ['banner_image', 'title', 'text', 'hide_text', 'url', 'show_for_anonymous_users', 'show_for_logged_in_users']
		widgets = {
			'banner_image': forms.HiddenInput()
		}


class BannerImageForm(forms.ModelForm):
	class Meta:
		model = BannerImage
		fields = ['image']
