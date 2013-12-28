from django import forms

class NewTopicForm(forms.Form):
	title = forms.CharField()
	body = forms.CharField(widget=forms.Textarea(attrs={'class': 'notes'}), help_text="No HTML or BBCode please. URLs will be link-ified")
