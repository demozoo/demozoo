from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from zxdemo.models import NewsItem, Article


admin.site.register(NewsItem)
admin.site.register(Article)
