from django import forms

from comments.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
