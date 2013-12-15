from django import forms

from comments.models import ProductionComment

class ProductionCommentForm(forms.ModelForm):
	class Meta:
		model = ProductionComment
		fields = ['body']
