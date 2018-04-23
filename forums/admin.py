from django.contrib import admin

from forums.models import Topic, Post


class PostInline(admin.TabularInline):
	model = Post

admin.site.register(
	Topic,
	inlines=[PostInline],
	search_fields=['title']
)
