# Import from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import pymysql
import re
from django.contrib.auth.models import User
from demoscene.models import *
from dataexchange import demozoo0

PUNCTUATION_REGEX = r'[\s\-\#\:\!\'\.\[\]\(\)\=\?\_]'

# mapping of DZ0 to DZ2 prod types:
# "a production of type X might actually be listed under any of the following types in DZ2"

PRODUCTION_TYPE_SUGGESTIONS = {
	1: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 32b intro => 32b-4K intro
	2: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 64b intro => 32b-4K intro
	3: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 128b intro => 32b-4K intro
	4: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 256b intro => 32b-4K intro
	5: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 512b intro => 32b-4K intro
	6: [15, 16, 18, 19, 20, 21, 37, 3, 27, 28], # 1k intro => 32b-4K intro
	7: [15, 16, 18, 19, 20, 21, 37, 3, 35, 27, 28], # 4k intro => 32b-16K intro
	8: [3, 35, 22, 10, 2, 4, 13, 1, 27, 28], # 8k intro => 4k-64k intro, intro, cracktro, demo
	9: [3, 35, 22, 10, 2, 4, 13, 1, 27, 28], # 16k intro
	10: [3, 35, 22, 10, 2, 4, 13, 1, 27, 28], # 32k intro
	11: [3, 35, 22, 10, 2, 4, 13, 1, 27, 28], # 40k intro
	12: [3, 35, 22, 10, 2, 4, 13, 1, 27, 28], # 64k intro
	13: [3, 35, 22, 10, 2, 4, 13, 1], # 80k intro
	14: [3, 35, 22, 10, 2, 4, 13, 1], # 96k intro
	15: [3, 35, 22, 10, 2, 4, 13, 1], # 100k intro
	16: [3, 35, 22, 10, 2, 4, 13, 1], # 128k intro
	17: [3, 35, 22, 10, 2, 4, 13, 1], # 256k intro
	18: [1, 8, 9], # artpack => demo, slideshow, pack
	19: [3, 35, 22, 10, 2, 4, 13, 1], # bbstro => general intros
	20: [3, 35, 22, 10, 2, 4, 13, 1], # cracktro
	21: [1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 16, 18, 19, 20, 21, 22, 27, 28, 35, 37], # demo
	22: [1, 9], # demopack
	23: [6], # demotool
	24: [1, 2, 3, 4, 10, 11, 13, 22, 35], # dentro
	25: [5], # diskmag
	26: [1], # fastdemo
	27: [33], # game
	28: [2, 3, 10, 11, 13, 15, 16, 18, 19, 20, 21, 22, 27, 28, 35, 37], # intro
	29: [1, 2, 3, 10, 11, 22, 35], # invitation
	30: [34], # liveact
	31: [1, 7, 12], # musicdisk
	32: [1], # report
	33: [1, 8], # slideshow
	34: [1, 7, 8, 9], # votedisk
	35: [34], # video
	36: [14, 29, 30, 31, 32, 38], # music
	37: [23, 24, 25, 26, 27, 28, 36], # graphics
	38: [25], # ascii collection
}

PLATFORM_SUGGESTIONS = {
	 2: [8], # BeOS
	 3: [7], # Linux
	 4: [4], # MS-Dos
	 5: [1], # Windows
	 6: [4], # MS-Dos/gus
	 7: [9,17], # Atari ST
	 8: [5,6,26], # Amiga AGA
	 9: [9,17], # Atari STe
	10: [5,6,26], # Amiga ECS
	11: [12,18], # Java
	12: [13,28,29], # Playstation
	13: [3], # Commodore 64
	14: [12,13,14,15,18,20,22,23,24,25,27,28,29,30,32], # Wild
	15: [-1], # Amstrad CPC
	16: [5,6,26], # Amiga PPC/RTG
	17: [9,17], # Atari Falcon 030
	18: [14,30], # Gameboy
	19: [2], # ZX Spectrum
	20: [10], # MacOS X
	21: [10], # MacOS
	22: [14,30], # Gameboy Advance
	23: [14,30], # Gameboy Color
	24: [23,14], # Dreamcast
	25: [-1], # SNES/Super Famicom
	26: [22], # SEGA Genesis/Mega Drive
	27: [12], # Flash
	28: [-1], # Oric
	29: [18], # Mobile Phone
	30: [21], # VIC 20
	31: [28], # Playstation 2
	32: [27], # TI-8x
	33: [5,6,26], # Atari TT 030
	34: [-1], # Acorn
	35: [12], # JavaScript
	36: [12], # Alambik
	37: [-1], # NEC TurboGrafx/PC Engine
	38: [15], # XBOX
	39: [14,18,27], # PalmOS
	40: [24], # Nintendo 64
	41: [-1], # C16/116/plus4
	42: [14,18], # PocketPC
	43: [12], # PHP
	44: [31], # MSX
	45: [14], # GamePark GP32
	46: [16], # Atari XL/XE
	47: [-1], # Intellivision
	48: [-1], # Thomson
	49: [-1], # Apple II GS
	50: [-1], # SEGA Master System
	51: [25], # NES/Famicom
	52: [24], # Gamecube
	53: [14], # GamePark GP2X
	54: [16], # Atari VCS
	55: [14], # Virtual Boy
	56: [-1], # BK-0010/11M
	57: [14], # Pokemon Mini
	58: [14], # SEGA Game Gear
	59: [-1], # Vectrex
	60: [14,18], # iPod
	61: [29], # Playstation Portable
	62: [32], # Nintendo DS
	63: [9,17], # Atari Jaguar
	64: [-1], # Wonderswan
	65: [14], # NeoGeo Pocket
	66: [15], # XBOX 360
	67: [14], # Atari Lynx
	68: [3,14], # C64 DTV
	69: [-1], # Amstrad Plus
	70: [7], # FreeBSD
	71: [7], # Solaris
	72: [5,6,26], # Amiga OCS
	73: [2], # Sam Coupe
#	74: [], # NULL
	75: [-1], # Spectravideo 3x8
	76: [-1], # Apple IIe
	77: [10], # MacOSX Intel
	78: [-1], # Playstation 3
	79: [24], # Nintendo Wii
	80: [7], # SGI/IRIX
	81: [-1], # BBC Micro
	82: [31], # MSX2/2+/Turbo-R
	83: [2], # Sam Coupe
	84: [-1], # TRS-80/CoCo
	85: [31], # MSX Turbo-R
	86: [-1], # Enterprise
	87: [31], # MSX 2 plus
	88: [2], # ZX-81
	89: [12], # Processing
}

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
	
	def find_matching_nicks_in_dz2_by_names(self, names):
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
		nick_ids = self.find_matching_nicks_in_dz2_by_names(author_names).values_list('id', flat=True)
		if not nick_ids:
			return
		
		# get all dz2 prodtype IDs that might conceivably match against any of the prodtypes for this prod
		dz2_type_ids = []
		for dz0_type_id in demozoo0.production_type_ids_for_production(production_info['id']):
			dz2_type_ids += PRODUCTION_TYPE_SUGGESTIONS[dz0_type_id]
		dz2_type_ids = tuple(set(dz2_type_ids))
		
		# ditto for platform IDs
		dz2_platform_ids = []
		for dz0_platform_id in demozoo0.platform_ids_for_production(production_info['id']):
			dz2_platform_ids += PLATFORM_SUGGESTIONS[dz0_platform_id]
		dz2_platform_ids = tuple(set(dz2_platform_ids))
		
		return list(
			Production.objects.raw('''
				SELECT DISTINCT demoscene_production.* FROM demoscene_production
				INNER JOIN demoscene_production_types ON (
					demoscene_production.id = demoscene_production_types.production_id
					AND demoscene_production_types.productiontype_id IN %s
				)
				LEFT JOIN demoscene_production_platforms ON demoscene_production.id = demoscene_production_platforms.production_id
				INNER JOIN demoscene_production_author_nicks ON (demoscene_production.id = demoscene_production_author_nicks.production_id)
				INNER JOIN demoscene_production_author_affiliation_nicks ON (demoscene_production.id = demoscene_production_author_affiliation_nicks.production_id)
				WHERE
					regexp_replace(LOWER(title), %s, '', 'g') = %s
					AND (demoscene_production_platforms.platform_id IN %s OR demoscene_production_platforms.platform_id IS NULL)
					AND (
						demoscene_production_author_nicks.nick_id IN %s
						OR demoscene_production_author_affiliation_nicks.nick_id IN %s
					)
			''', (dz2_type_ids, PUNCTUATION_REGEX, self.depunctuate(production_info['name']), dz2_platform_ids, tuple(nick_ids), tuple(nick_ids)) )
		)
	
	# Only to be used as secondary confirmation! (e.g. inferring that two same-named releasers are the same, on the basis that they've released a same-named production)
	def find_matching_production_in_dz2_by_title(self, production_info):
		# get all dz2 prodtype IDs that might conceivably match against any of the prodtypes for this prod
		dz2_type_ids = []
		for dz0_type_id in demozoo0.production_type_ids_for_production(production_info['id']):
			dz2_type_ids += PRODUCTION_TYPE_SUGGESTIONS[dz0_type_id]
		dz2_type_ids = tuple(set(dz2_type_ids))
		
		# ditto for platform IDs
		dz2_platform_ids = []
		for dz0_platform_id in demozoo0.platform_ids_for_production(production_info['id']):
			dz2_platform_ids += PLATFORM_SUGGESTIONS[dz0_platform_id]
		dz2_platform_ids = tuple(set(dz2_platform_ids))
		
		return list(
			Production.objects.raw('''
				SELECT DISTINCT demoscene_production.* FROM demoscene_production
				INNER JOIN demoscene_production_types ON (
					demoscene_production.id = demoscene_production_types.production_id
					AND demoscene_production_types.productiontype_id IN %s
				)
				LEFT JOIN demoscene_production_platforms ON demoscene_production.id = demoscene_production_platforms.production_id
				WHERE
					regexp_replace(LOWER(title), %s, '', 'g') = %s
					AND (demoscene_production_platforms.platform_id IN %s OR demoscene_production_platforms.platform_id IS NULL)
			''', (dz2_type_ids, PUNCTUATION_REGEX, self.depunctuate(production_info['name']), dz2_platform_ids) )
		)
	
	def find_matching_production_in_dz2(self, production_info, loose = False):
		
		if loose:
			strategies = (
				'find_matching_production_in_dz2_by_pouet_id',
				'find_matching_production_in_dz2_by_csdb_id',
				'find_matching_production_in_dz2_by_title',
			)
		else:
			strategies = (
				'find_matching_production_in_dz2_by_pouet_id',
				'find_matching_production_in_dz2_by_csdb_id',
				'find_matching_production_in_dz2_by_title_and_author_names',
			)
		
		for strategy in strategies:
			results = getattr(self, strategy)(production_info)
			if not results:
				continue
			if len(results) > 1 and not loose:
				raise Exception(
					'Multiple matches found for [%s] %s using strategy %s: %s' %
					(production_info['id'], production_info['name'], strategy, [prod.id for prod in results])
				)
			for result in results:
				print "(%s) %s => (%s) %s (by %s)" % (
					production_info['id'],
					production_info['name'],
					result.id, result.title,
					strategy
				)
			return results
		
		return []
	
	def find_matching_releaser_in_dz2_by_demozoo0_id(self, releaser_info):
		return Releaser.objects.filter(demozoo0_id = releaser_info['id'])
	
	def find_matching_releaser_in_dz2_by_slengpung_id(self, releaser_info):
		if releaser_info['slengpung_id'] != None:
			return Releaser.objects.filter(slengpung_user_id = releaser_info['slengpung_id'])
	
	def find_matching_releaser_in_dz2_by_name_and_releases(self, releaser_info):
		dz0_prods_by_releaser = demozoo0.productions_by_releaser(releaser_info['id'])
		
		dz2_prods_by_releaser = []
		for dz0_prod in dz0_prods_by_releaser:
			dz2_prods_by_releaser += self.find_matching_production_in_dz2(dz0_prod, loose = True)
		
		candidates = Releaser.objects.extra(
			tables = ['demoscene_nick','demoscene_nickvariant'],
			where = [
				"demoscene_releaser.id = demoscene_nick.releaser_id",
				"demoscene_nick.id = demoscene_nickvariant.nick_id",
				"regexp_replace(LOWER(demoscene_nickvariant.name) , %s, '', 'g') = %s"
			],
			params = (PUNCTUATION_REGEX, self.depunctuate(releaser_info['name']) )
		)
		matches = []
		for releaser in candidates:
			for prod in dz2_prods_by_releaser:
				if prod and prod in releaser.productions():
					matches.append(releaser)
					break
		
		return matches

	def find_matching_releaser_in_dz2(self, releaser_info):
		for strategy in (
			'find_matching_releaser_in_dz2_by_demozoo0_id',
			'find_matching_releaser_in_dz2_by_slengpung_id',
			'find_matching_releaser_in_dz2_by_name_and_releases',
		):
			results = getattr(self, strategy)(releaser_info)
			if not results:
				continue
			if len(results) == 1:
				print "(%s) %s => %s (by %s)" % (
					releaser_info['id'],
					releaser_info['name'],
					results[0],
					strategy
				)
				return results[0]
			else:
				raise Exception(
					'Multiple matches found for [%s] %s using strategy %s: %s' %
					(releaser_info['id'], releaser_info['name'], strategy, [releaser.id for releaser in results])
				)
	
	def handle_noargs(self, **options):
		import sys
		import codecs
		sys.stdout = codecs.getwriter('utf8')(sys.stdout)
		
		# pending approval from Pouet:
		# self.import_all_users()
		# self.import_all_party_series()
		# self.import_all_releasers()
		
		#for info in demozoo0.all_productions():
		#	match = self.find_matching_production_in_dz2(info)
		for info in demozoo0.releasers_with_credits():
			match = self.find_matching_releaser_in_dz2(info)
