from django.contrib import admin
from demoscene.models import *

admin.site.register(ProductionType)
admin.site.register(Platform)
admin.site.register(Production, list_display = ("title",))
