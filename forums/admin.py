from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from forums.models import Post, Topic


class PostInline(admin.TabularInline):
    model = Post


admin.site.register(
    Topic,
    inlines=[PostInline],
    search_fields=['title']
)
