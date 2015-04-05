from django.contrib import admin

from homepage.models import Banner, NewsStory, NewsImage


admin.site.register(Banner, list_display=('title', 'show_for_anonymous_users', 'show_for_logged_in_users', 'created_at'))
admin.site.register(NewsStory, list_display=('title', 'created_at'))
admin.site.register(NewsImage, list_display=['image_tag'])
