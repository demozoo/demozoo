from __future__ import absolute_import, unicode_literals

from django import forms

from forums.models import Post

class NewTopicForm(forms.Form):
    title = forms.CharField(max_length=255)
    body = forms.CharField(widget=forms.Textarea(attrs={'class': 'notes'}), help_text="No HTML or BBCode please. URLs will be link-ified")

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body']
