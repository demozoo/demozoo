from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from pages.models import Page

admin.site.register(Page, prepopulated_fields = {'slug': ('title',)} )
