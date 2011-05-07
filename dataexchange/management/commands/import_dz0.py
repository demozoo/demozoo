# Import from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import pymysql
import re
from django.contrib.auth.models import User
from demoscene.models import *
from dataexchange import demozoo0

PUNCTUATION_REGEX = r'[\s\-\#\:\!\'\.\[\]\(\)\=\?\_]'

class Command(NoArgsCommand):
	def import_all_users(self):
		print "importing users"
		cur = self.dz0_db.cursor()
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
	
	def import_all_party_series(self):
		print "importing party series"
		cur = self.dz0_db.cursor()
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
	
	def import_all_releasers(self): # INCOMPLETE
		cur = self.dz0_db.cursor()
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
	
	# strip punctuation and whitespace that's likely going to obscure string-to-string matches
	def depunctuate(self, str):
		return re.sub(PUNCTUATION_REGEX, '', str.lower())
	
	def find_matching_releasers_in_dz2_by_names(self, names):
		return Nick.objects.extra(
			tables = ['demoscene_nickvariant'],
			where = [
				"demoscene_nick.id = demoscene_nickvariant.nick_id",
				"regexp_replace(LOWER(demoscene_nickvariant.name) , %s, '', 'g') IN %s"
			],
			params = (PUNCTUATION_REGEX, tuple(names))
		)
	
	def find_matching_production_in_dz2(self, production_info):
		#id_matches = Production.objects.filter(demozoo0_id = production_info['id'])
		#if len(id_matches) == 1:
		#	print "[%s] %s - already found by ID" % (production_info['id'], production_info['name'])
		#	return
		#elif len(id_matches) > 1:
		#	print "[%s] %s - multiple matches by ID!" % (production_info['id'], production_info['name'])
		#	return
		
		if production_info['pouet_id'] != None:
			pouet_id_matches = Production.objects.filter(pouet_id = production_info['pouet_id'])
			if len(pouet_id_matches) == 1:
				print "[%s] %s - found by Pouet ID" % (production_info['id'], production_info['name'])
				#if self.depunctuate(pouet_id_matches[0].title) != self.depunctuate(production_info['name']):
				#	print "[%s] - %s vs %s" % (production_info['id'], production_info['name'], pouet_id_matches[0].title)
				return
			elif len(pouet_id_matches) > 1:
				print "[%s] %s - multiple matches by Pouet ID!" % (production_info['id'], production_info['name'])
				return
		
		if production_info['csdb_id'] != None:
			csdb_id_matches = Production.objects.filter(csdb_id = production_info['csdb_id'])
			if len(csdb_id_matches) == 1:
				print "[%s] %s - found by csdb ID" % (production_info['id'], production_info['name'])
				#if self.depunctuate(csdb_id_matches[0].title) != self.depunctuate(production_info['name']):
				#	print "[%s] - %s vs %s" % (production_info['id'], production_info['name'], csdb_id_matches[0].title)
				return
			elif len(csdb_id_matches) > 1:
				print "[%s] %s - multiple matches by csdb ID!" % (production_info['id'], production_info['name'])
				return
		
		# get all names of all releasers of this production
		author_names = [
			self.depunctuate(name)
			for name in demozoo0.author_and_affiliation_names(production_info['id'])
		]
		
		if author_names:
			# find IDs of all nicks that match those names in any variant
			nick_ids = self.find_matching_releasers_in_dz2_by_names(author_names).values_list('id', flat=True)
			
			if nick_ids:
				title_matches = list(
					Production.objects.raw('''
						SELECT DISTINCT demoscene_production.* FROM demoscene_production
						INNER JOIN demoscene_production_author_nicks ON (demoscene_production.id = demoscene_production_author_nicks.production_id)
						INNER JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production.id = demoscene_production_author_affiliation_nicks.production_id)
						WHERE
							regexp_replace(LOWER(title), %s, '', 'g') = %s
							AND (
								demoscene_production_author_nicks.nick_id IN %s
								OR demoscene_production_author_affiliation_nicks.nick_id IN %s
							)
					''', (PUNCTUATION_REGEX, self.depunctuate(production_info['name']), tuple(nick_ids), tuple(nick_ids)) )
				)
				if len(title_matches) == 1:
					print "[%s] %s - found by title" % (production_info['id'], production_info['name'])
					return
				elif len(title_matches) > 1:
					print "[%s] %s - multiple matches by title!" % (production_info['id'], production_info['name'])
					return
		
		#print "[%s] %s - no match" % (production_info['id'], production_info['name'])
		
	def handle_noargs(self, **options):
		import sys
		import codecs
		sys.stdout = codecs.getwriter('utf8')(sys.stdout)
		self.dz0_db = pymysql.connect(user="root", db="demozoo_production", charset="latin1")
		
		# pending approval from Pouet:
		# self.import_all_users()
		# self.import_all_party_series()
		# self.import_all_releasers()
		
		for info in demozoo0.all_productions():
			self.find_matching_production_in_dz2(info)
		
		self.dz0_db.close()
