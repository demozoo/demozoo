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
    residue = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)

    def user_can_reply(self, user):
        return user.is_authenticated and (not self.locked or user.is_staff)

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
        return "%s#post-%d" % (reverse('forums_post', args=[str(self.id)]), self.id)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        last_topic_post = self.topic.posts.order_by("created_at").last()
        if last_topic_post:
            self.topic.last_post_at = last_topic_post.created_at
            self.topic.last_post_by_user = last_topic_post.user
            self.topic.reply_count = self.topic.posts.count() - 1
            self.topic.save()
        else:
            self.topic.delete()
