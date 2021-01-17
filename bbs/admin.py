from django.contrib import admin

from bbs.models import BBS

admin.site.register(BBS, raw_id_fields=['bbstros'])
