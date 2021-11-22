from django.contrib import admin

from zxdemo.models import Article, NewsItem


admin.site.register(NewsItem)
admin.site.register(Article)
