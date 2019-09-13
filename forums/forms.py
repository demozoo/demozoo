from django import forms

from forums.models import Post

class NewTopicForm(forms.Form):
    title = forms.CharField()
    body = forms.CharField(widget=forms.Textarea(attrs={'class': 'notes'}), help_text="No HTML or BBCode please. URLs will be link-ified")

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body']
