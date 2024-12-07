from django.contrib import admin

from forums.models import Post, Topic


class PostInline(admin.TabularInline):
    model = Post
    raw_id_fields = ["user"]


admin.site.register(
    Topic, inlines=[PostInline], search_fields=["title"], raw_id_fields=["created_by_user", "last_post_by_user"]
)
