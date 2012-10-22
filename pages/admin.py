from django.contrib import admin

from pages.models import *

admin.site.register(Page, prepopulated_fields = {'slug': ('title',)} )
