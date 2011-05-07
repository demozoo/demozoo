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
		for row in demozoo0.all_users():
			try:
				profile = AccountProfile.objects.get(demozoo0_id = row['id'])
			except AccountProfile.DoesNotExist:
				user = User(
					username = "%s [dz0]" % row['nick'],
					email = (row['email'] or ''),
					is_staff = False,
					is_active = False,
					is_superuser = False,
					date_joined = row['created_at']
				)
				user.save()
				profile = AccountProfile(
					user = user,
					edit_mode_active = False,
					sticky_edit_mode = False,
					demozoo0_id = row['id']
				)
				profile.save()
	
	def import_all_party_series(self):
		print "importing party series"
		for row in demozoo0.all_party_series():
			try:
				party_series = PartySeries.objects.get(demozoo0_ids = row['id'])
			except PartySeries.DoesNotExist:
				try:
					# search by pouet ID
					party_series = PartySeries.objects.get(pouet_party_id = row['pouet_id'])
				except PartySeries.DoesNotExist:
					try:
						# search by name - needed because we don't allow duplicate names
						party_series = PartySeries.objects.get(name = row['name'])
					except PartySeries.DoesNotExist:
						# create new
						party_series = PartySeries(
							name = row['name'],
							website = (row['website'] or ''),
							pouet_party_id = row['pouet_id'],
						)
						
				if website and not party_series.website:
					party_series.website = row['website']
				party_series.save()
				dz0_id = PartySeriesDemozoo0Reference(
					demozoo0_id = row['id'],
					party_series = party_series
				)
				dz0_id.save()
	
	def import_all_releasers(self): # INCOMPLETE
		print "importing releasers"
		for (id, type, pouet_id, zxdemo_id, name, abbreviation, website, csdb_id, country_id, slengpung_id) in demozoo0.all_releasers():
			try:
				releaser = Releaser.objects.get(demozoo0_id = row['id'])
				#print "%s - %s; found by demozoo0_id" % (row['id'], row['name'])
			except Releaser.DoesNotExist:
				if row['type'] == 'Scener' and row['slengpung_id']:
					try:
						releaser = Releaser.objects.get(slengpung_user_id = row['slengpung_id'])
						print "%s found by slengpung ID" % row['name']
					except Releaser.DoesNotExist:
						pass
				#print "Looking for %s - %s (%s)" % (row['id'], row['name'], row['type'])
				#name_match_count = Releaser.objects.filter(nicks__variants__name = row['name'], is_group = (row['type'] == 'Group')).count()
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
	
	# not usable yet, because we don't have a demozoo0_id field in productions yet...
	def find_matching_production_in_dz2_by_dz0_id(self, production_info):
		return Production.objects.filter(demozoo0_id = production_info['id'])
	
	def find_matching_production_in_dz2_by_pouet_id(self, production_info):
		if production_info['pouet_id'] != None:
			return Production.objects.filter(pouet_id = production_info['pouet_id'])
	
	def find_matching_production_in_dz2_by_csdb_id(self, production_info):
		if production_info['csdb_id'] != None:
			return Production.objects.filter(csdb_id = production_info['csdb_id'])
	
	def find_matching_production_in_dz2_by_title_and_author_names(self, production_info):
		# get all names of all releasers of this production
		author_names = [
			self.depunctuate(name)
			for name in demozoo0.author_and_affiliation_names(production_info['id'])
		]
		if not author_names:
			return
		
		# find IDs of all nicks that match those names in any variant
		nick_ids = self.find_matching_releasers_in_dz2_by_names(author_names).values_list('id', flat=True)
		if not nick_ids:
			return
		
		return list(
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
	
	def find_matching_production_in_dz2(self, production_info):
		
		for strategy in (
			'find_matching_production_in_dz2_by_pouet_id',
			'find_matching_production_in_dz2_by_csdb_id',
			'find_matching_production_in_dz2_by_title_and_author_names',
		):
			results = getattr(self, strategy)(production_info)
			if not results:
				continue
			if len(results) == 1:
				return results[0]
			else:
				raise Exception(
					'Multiple matches found for [%s] %s using strategy %s' %
					(production_info['id'], production_info['name'], strategy)
				)
		
	def handle_noargs(self, **options):
		import sys
		import codecs
		sys.stdout = codecs.getwriter('utf8')(sys.stdout)
		
		# pending approval from Pouet:
		# self.import_all_users()
		# self.import_all_party_series()
		# self.import_all_releasers()
		
		for info in demozoo0.all_productions():
			print "(%s) %s => %s" % (
				info['id'],
				info['name'],
				self.find_matching_production_in_dz2(info)
			)
