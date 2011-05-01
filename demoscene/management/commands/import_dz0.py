# Import from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import pymysql
from django.contrib.auth.models import User
from demoscene.models import AccountProfile

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		dz0 = pymysql.connect(user="root", db="demozoo_production")
		
		print "importing users"
		cur = dz0.cursor()
		cur.execute("SELECT id, email, created_at, nick FROM users")
		for (id, email, created_at, nick) in cur:
			try:
				profile = AccountProfile.objects.get(demozoo0_id = id)
			except AccountProfile.DoesNotExist:
				user = User(
					username = "%s [dz0]" % nick,
					email = (email or ''),
					is_staff = False,
					is_active = False,
					is_superuser = False,
					date_joined = created_at
				)
				user.save()
				profile = AccountProfile(
					user = user,
					edit_mode_active = False,
					sticky_edit_mode = False,
					demozoo0_id = id
				)
				profile.save()
		
		cur.close()
		dz0.close()
