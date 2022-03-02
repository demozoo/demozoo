from django import forms

from homepage.models import Banner, BannerImage, NewsImage, NewsStory


class NewsStoryForm(forms.ModelForm):
    class Meta:
        model = NewsStory
        fields = ['title', 'image', 'text', 'is_public']
        widgets = {
            'image': forms.HiddenInput()
        }


class NewsImageForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = NewsImage
        fields = ['image']


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = [
            'banner_image', 'title', 'text', 'hide_text', 'url',
            'small_print',
            'show_for_anonymous_users', 'show_for_logged_in_users'
        ]
        widgets = {
            'banner_image': forms.HiddenInput(),
            'text': forms.Textarea(attrs={'rows': 4, 'style': 'height: auto;'}),
            'small_print': forms.Textarea(attrs={'rows': 4, 'style': 'height: auto;'}),
        }


class BannerImageForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = BannerImage
        fields = ['image']
