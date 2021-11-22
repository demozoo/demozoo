from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Topic(models.Model):
    title = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by_user = models.ForeignKey(
        User, related_name='forum_topics', null=True, blank=True, on_delete=models.SET_NULL
    )

    last_post_at = models.DateTimeField()
    last_post_by_user = models.ForeignKey(User, related_name='+', null=True, blank=True, on_delete=models.SET_NULL)

    reply_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('forums_topic', args=[str(self.id)])


class Post(models.Model):
    user = models.ForeignKey(User, related_name='forum_posts', on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name='posts', on_delete=models.CASCADE)

    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('forums_post', args=[str(self.id)])
