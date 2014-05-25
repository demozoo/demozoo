from django import forms

from comments.models import Comment

class ProductionCommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ['body']
