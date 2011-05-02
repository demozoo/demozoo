# Import from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import pymysql
from django.contrib.auth.models import User
from demoscene.models import AccountProfile, Releaser, PartySeries, PartySeriesDemozoo0Reference

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
		
		print "importing party series"
		cur = dz0.cursor()
		cur.execute("SELECT id, name, website, pouet_id FROM party_series WHERE name IS NOT NULL")
		for (id, name, website, pouet_id) in cur:
			try:
				party_series = PartySeries.objects.get(demozoo0_ids = id)
			except PartySeries.DoesNotExist:
				try:
					# search by pouet ID
					party_series = PartySeries.objects.get(pouet_party_id = pouet_id)
				except PartySeries.DoesNotExist:
					try:
						# search by name - needed because we don't allow duplicate names
						party_series = PartySeries.objects.get(name = name)
					except PartySeries.DoesNotExist:
						# create new
						party_series = PartySeries(
							name = name,
							website = (website or ''),
							pouet_party_id = pouet_id,
						)
						
				if website and not party_series.website:
					party_series.website = website
				party_series.save()
				dz0_id = PartySeriesDemozoo0Reference(
					demozoo0_id = id,
					party_series = party_series
				)
				dz0_id.save()
		
		print "importing releasers"
		cur.execute('''
			SELECT id, type, pouet_id, zxdemo_id, name, abbreviation, website, csdb_id, country_id, slengpung_id
			FROM releasers
		''')
		for (id, type, pouet_id, zxdemo_id, name, abbreviation, website, csdb_id, country_id, slengpung_id) in cur:
			try:
				releaser = Releaser.objects.get(demozoo0_id = id)
				#print "%s - %s; found by demozoo0_id" % (id, name)
			except Releaser.DoesNotExist:
				if type == 'Scener' and slengpung_id:
					try:
						releaser = Releaser.objects.get(slengpung_user_id = slengpung_id)
						print "%s found by slengpung ID" % name
					except Releaser.DoesNotExist:
						pass
				#print "Looking for %s - %s (%s)" % (id, name, type)
				#name_match_count = Releaser.objects.filter(nicks__variants__name = name, is_group = (type == 'Group')).count()
				#print "%s matches by name" % name_match_count
		
		cur.close()
		dz0.close()
