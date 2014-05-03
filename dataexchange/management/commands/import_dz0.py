# Import from Demozoo v0 MySQL database

from django.core.management.base import NoArgsCommand

import sys
import re
from django.contrib.auth.models import User
from demoscene.models import *
from parties.models import *
from platforms.models import Platform
from dataexchange import demozoo0
import datetime

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

# Map dz0 ID to (dz2 ID, tag to add)
PRODUCTION_TYPE_DZ0_TO_DZ2 = {
	1: (15, None), # 32b intro
	2: (16, None), # 64b intro
	3: (18, None), # 128b intro
	4: (19, None), # 256b intro
	5: (20, None), # 512b intro
	6: (21, None), # 1k intro
	7: (3, None), # 4k intro
	8: (35, '8k'), # 8k intro
	9: (35, None), # 16k intro
	10: (22, None), # 32k intro
	11: (10, None), # 40k intro
	12: (2, None), # 64k intro
	13: (4, '80k'), # 80k intro
	14: (4, '96k'), # 96k intro
	15: (4, '100k'), # 100k intro
	16: (4, '128k'), # 128k intro
	17: (4, '256k'), # 256k intro
	18: (8, None), # artpack
	19: (41, None), # bbstro
	20: (13, None), # cracktro
	21: (1, None), # demo
	22: (9, None), # demopack
	23: (6, None), # demotool
	24: (1, 'dentro'), # dentro
	25: (5, None), # diskmag
	26: (1, 'fastdemo'), # fastdemo
	27: (33, None), # game
	28: (4, None), # intro
	29: (None, 'invitation'), # invitation
	30: (42, None), # liveact
	31: (7, None), # musicdisk
	32: (None, 'report'), # report
	33: (8, None), # slideshow
	34: (1, 'votedisk'), # votedisk
	35: (34, None), # video
	36: (14, None), # music
	37: (23, None), # graphics
	38: (25, None), # ascii collection
}

PLATFORM_DZ0_TO_DZ2 = {
	2: None, # BeOS
	3: 7, # Linux
	4: 4, # MS-Dos
	5: 1, # Windows
	6: 4, # MS-Dos/gus
	7: 9, # Atari ST
	8: 6, # Amiga AGA
	9: 9, # Atari STe
	10: 5, # Amiga ECS
	11: 33, # Java
	12: 13, # Playstation
	13: 3, # Commodore 64
	14: None, # Wild
	15: 33, # Amstrad CPC
	16: 26, # Amiga PPC/RTG
	17: 17, # Atari Falcon 030
	18: 14, # Gameboy
	19: 2, # ZX Spectrum
	20: 10, # MacOS X
	21: 33, # MacOS
	22: 30, # Gameboy Advance
	23: 14, # Gameboy Color
	24: 23, # Dreamcast
	25: 33, # SNES/Super Famicom
	26: 22, # Sega Genesis/Mega Drive
	27: 12, # Flash
	28: 33, # Oric
	29: 18, # Mobile Phone
	30: 21, # VIC 20
	31: 28, # Playstation 2
	32: 27, # TI-8x
	33: 33, # Atari TT 030
	34: 33, # Acorn
	35: 12, # JavaScript
	36: 12, # Alambik
	37: 33, # NEC TurboGrafx/PC Engine
	38: 33, # XBOX
	39: 18, # PalmOS
	40: 33, # Nintendo 64
	41: 33, # C16/116/plus4
	42: 18, # PocketPC
	43: 12, # PHP
	44: 31, # MSX
	45: 14, # Gamepark GP32
	46: 16, # Atari XL/XE
	47: 33, # Intellivision
	48: 33, # Thomson
	49: 33, # Apple II GS
	50: 33, # Sega Master System
	51: 25, # NES/Famicom
	52: 33, # Gamecube
	53: 14, # GamePark GP2X
	54: 16, # Atari VCS
	55: 33, # Virtual Boy
	56: 33, # BK-0010/11M
	57: 18, # Pokemon Mini
	58: 18, # SEGA Game Gear
	59: 33, # Vectrex
	60: 18, # iPod
	61: 29, # Playstation Portable
	62: 32, # Nintendo DS
	63: 33, # Atari Jaguar
	64: 18, # Wonderswan
	65: 18, # NeoGeo Pocket
	66: 15, # XBOX 360
	67: 18, # Atari Lynx
	68: 33, # C64 DTV
	69: 33, # Amstrad Plus
	70: None, # FreeBSD
	71: None, # Solaris
	72: 5, # Amiga OCS
	73: 33, # Sam Coupe
	74: None, # NULL
	75: 31, # Spectravideo 3x8
	76: 33, # Apple IIe
	77: 10, # MacOSX Intel
	78: 33, # Playstation 3
	79: 24, # Nintendo Wii
	80: None, # SGI/IRIX
	81: 33, # BBC Micro
	82: 31, # MSX2/2+/Turbo-R
	83: 33, # Sam Coupe
	84: 33, # TRS-80/CoCo
	85: 31, # MSX Turbo-R
	86: 33, # Enterprise
	87: 31, # MSX 2 Plus
	88: 33, # ZX-81
	89: 33, # Processing
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
						# print "%s found by slengpung ID" % row['name']
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
		if not dz2_platform_ids:
			return
		
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
		dz2_platform_ids = [-1]
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
				'find_matching_production_in_dz2_by_dz0_id',
				'find_matching_production_in_dz2_by_pouet_id',
				'find_matching_production_in_dz2_by_csdb_id',
				'find_matching_production_in_dz2_by_title',
			)
		else:
			strategies = (
				'find_matching_production_in_dz2_by_dz0_id',
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
			#for result in results:
			#	print "(%s) %s => (%s) %s (by %s)" % (
			#		production_info['id'],
			#		production_info['name'],
			#		result.id, result.title,
			#		strategy
			#	)
			return results
		
		return []
	
	def find_or_create_production(self, production_info):
		print "finding %s" % production_info['name']
		matches = self.find_matching_production_in_dz2(production_info)
		if matches:
			production = matches[0]
			print u'- found %s' % production
			is_new = False
			if not production.demozoo0_id:
				production.demozoo0_id = production_info['id']
			if not production.pouet_id:
				production.pouet_id = production_info['pouet_id']
			if not production.csdb_id:
				production.csdb_id = production_info['csdb_id']
			if not production.zxdemo_id:
				production.zxdemo_id = production_info['zxdemo_id']
			if not production.scene_org_id:
				production.scene_org_id = production_info['scene_org_id']
		else:
			print "- not found"
			is_new = True
			
			dz0_platforms = demozoo0.platform_ids_for_production(production_info['id'])
			dz2_platforms = []
			for dz0_platform in dz0_platforms:
				dz2_platform = PLATFORM_DZ0_TO_DZ2.get(dz0_platform)
				if dz2_platform:
					dz2_platforms.append(dz2_platform)
			
			dz0_prod_types = demozoo0.production_type_ids_for_production(production_info['id'])
			dz2_prod_types = []
			tags = []
			for dz0_prod_type in dz0_prod_types:
				(dz2_prod_type, tag) = PRODUCTION_TYPE_DZ0_TO_DZ2.get(dz0_prod_type)
				if dz0_prod_type == 19:
					# special case: set dz2 prod type to bbstro if it's on DOS/Windows, intro otherwise
					if 1 in dz2_platforms or 4 in dz2_platforms:
						dz2_prod_types.append(41)
					else:
						dz2_prod_types.append(4)
				elif dz2_prod_type:
					dz2_prod_types.append(dz2_prod_type)
				if tag:
					tags.append(tag)
			
			if dz2_prod_types == [42] and not demozoo0.production_has_competition_placings(production_info['id']):
				print "live act, not in a competition - does not belong in dz2"
				return None
			
			if dz2_prod_types == [] and 32 in dz0_prod_types: # report
				if dz2_platforms == [34]: # platform = video
					if demozoo0.production_has_competition_placings(production_info['id']):
						# appeared in a competition
						dz2_prod_types.append(34)
						tags.append('report')
					else:
						print "video report not in a competition - does not belong in dz2"
						return None
				else:
					# some non-video platform - add as a demo
					dz2_prod_types.append(1)
					tags.append('report')
			
			if dz2_prod_types == [] and 29 in dz0_prod_types: # invitation
				dz2_prod_types.append(1) # demo
			
			production = Production(
				title = production_info['name'],
				demozoo0_id = production_info['id'],
				pouet_id = production_info['pouet_id'],
				csdb_id = production_info['csdb_id'],
				zxdemo_id = production_info['zxdemo_id'],
				scene_org_id = production_info['scene_org_id'],
				updated_at = datetime.datetime.now(),
				data_source = 'dz0'
			)
			if dz2_prod_types:
				production.supertype = ProductionType.objects.get(id = dz2_prod_types[0]).supertype
			else:
				production.supertype = 'production'
			
		# check that release dates agree as far as they go
		if production_info['release_date_precision']:
			dz0_date = FuzzyDate(
				production_info['release_date_datestamp'],
				production_info['release_date_precision'])
		else:
			dz0_date = None
		
		dz2_date = production.release_date
		
		if dz0_date:
			if not dz0_date.agrees_with(dz2_date):
				print "WARNING: dates do not agree. dz0 = %s, dz2 = %s" % (dz0_date, dz2_date)
			elif dz0_date.precision == 'd' and (dz2_date == None or dz2_date.precision in ['m','y']):
				production.release_date_date = datetime.date(dz0_date.date.year, dz0_date.date.month, dz0_date.date.day)
				production.release_date_precision = 'd'
			elif dz0_date.precision == 'm' and (dz2_date == None or dz2_date.precision == 'y'):
				production.release_date_date = datetime.date(dz0_date.date.year, dz0_date.date.month, 1)
				production.release_date_precision = 'm'
			elif dz0_date.precision == 'y' and dz2_date == None:
				production.release_date_date = datetime.date(dz0_date.date.year, 1, 1)
				production.release_date_precision = 'y'
		
		production.save()
		if is_new:
			production.types = ProductionType.objects.filter(id__in = dz2_prod_types)
			production.platforms = Platform.objects.filter(id__in = dz2_platforms)
			if tags:
				production.tags.add(*tags)
			
			last_affiliation_list = None
			for authorship in demozoo0.authorships_for_production(production_info['id']):
				releaser = self.find_or_create_releaser(authorship['releaser'])
				nick = self.find_or_create_nick_for_releaser(releaser, authorship['nick'])
				production.author_nicks.add(nick)
				
				affiliations = [affil for affil in demozoo0.affiliations_for_authorship(authorship['id'])]
				affiliation_list = [affil['nick']['id'] for affil in affiliations]
				if last_affiliation_list == None:
					last_affiliation_list = affiliation_list
					for affiliation in affiliations:
						affil_releaser = self.find_or_create_releaser(affiliation['releaser'])
						affil_nick = self.find_or_create_nick_for_releaser(affil_releaser, affiliation['nick'])
						production.author_affiliation_nicks.add(affil_nick)
				else:
					if last_affiliation_list != affiliation_list:
						print "WARNING: Different authors have different affiliations. Ignoring all but the first"
		
		downloads = demozoo0.download_links_for_production(production_info['id'])
		for download in downloads:
			if production.download_links.filter(url = download['url']).count():
				continue
			
			if len(downloads) == 1 or re.search(r'zxdemo\.org', download['url']) or production_info['pouet_id'] == None:
				pass
			elif download['description'] == None:
				pass
			elif (re.search(r'(fix|version|patched)', download['description']) or re.match(r'disk', download['description']) or download['description'] == 'final') and not re.search(r'(video|youtube)', download['description']):
				pass
			else:
				continue
			
			DownloadLink.objects.create(
				production_id = production.id,
				demozoo0_id = download['id'],
				url = download['url'],
				description = (download['description'] or '')
			)
		
		return production
	
	def find_matching_releaser_in_dz2_by_demozoo0_id(self, releaser_info):
		return Releaser.objects.filter(demozoo0_id = releaser_info['id'])
	
	def find_matching_releaser_in_dz2_by_slengpung_id(self, releaser_info):
		if releaser_info['slengpung_id'] != None:
			return Releaser.objects.filter(slengpung_user_id = releaser_info['slengpung_id'])
	
	# Only to be used as secondary confirmation!
	def find_matching_releaser_in_dz2_by_name(self, releaser_info):
		names = [self.depunctuate(name) for name in demozoo0.names_for_releaser(releaser_info['id'])]
		return Releaser.objects.extra(
			tables = ['demoscene_nick','demoscene_nickvariant'],
			where = [
				"demoscene_releaser.id = demoscene_nick.releaser_id",
				"demoscene_nick.id = demoscene_nickvariant.nick_id",
				"regexp_replace(LOWER(demoscene_nickvariant.name) , %s, '', 'g') IN %s",
				"demoscene_releaser.is_group = %s",
			],
			params = (PUNCTUATION_REGEX, tuple(names), (releaser_info['type'] == 'Group') )
		).distinct()
	
	def find_matching_releaser_in_dz2_by_name_and_releases(self, releaser_info):
		dz0_prods_by_releaser = demozoo0.productions_by_releaser(releaser_info['id'])
		
		dz2_prods_by_releaser = []
		for dz0_prod in dz0_prods_by_releaser:
			dz2_prods_by_releaser += self.find_matching_production_in_dz2(dz0_prod, loose = True)
		
		candidates = self.find_matching_releaser_in_dz2_by_name(releaser_info)
		matches = []
		for releaser in candidates:
			for prod in dz2_prods_by_releaser:
				if prod and prod in releaser.productions():
					matches.append(releaser)
					break
		
		return matches

	def find_matching_releaser_in_dz2_by_name_and_groups(self, releaser_info):
		dz0_groups_for_releaser = demozoo0.groups_for_releaser(releaser_info['id'])
		
		dz2_groups_for_releaser = []
		for dz0_group in dz0_groups_for_releaser:
			dz2_groups_for_releaser += self.find_matching_releaser_in_dz2(dz0_group, loose = True)
		
		candidates = self.find_matching_releaser_in_dz2_by_name(releaser_info)
		matches = []
		for releaser in candidates:
			for group in dz2_groups_for_releaser:
				if group and group in releaser.groups():
					matches.append(releaser)
					break
		
		return matches
	
	def find_matching_releaser_in_dz2_by_name_and_members(self, releaser_info):
		dz0_members_for_releaser = demozoo0.members_for_releaser(releaser_info['id'])
		
		dz2_members_for_releaser = []
		for dz0_member in dz0_members_for_releaser:
			dz2_members_for_releaser += self.find_matching_releaser_in_dz2(dz0_member, loose = True)
		
		candidates = self.find_matching_releaser_in_dz2_by_name(releaser_info)
		matches = []
		for releaser in candidates:
			for member in dz2_members_for_releaser:
				if member and member in releaser.members():
					matches.append(releaser)
					break
		
		return matches
	
	def find_matching_releaser_in_dz2(self, releaser_info, loose = False):
		if loose:
			strategies = (
				'find_matching_releaser_in_dz2_by_demozoo0_id',
				'find_matching_releaser_in_dz2_by_slengpung_id',
				'find_matching_releaser_in_dz2_by_name',
			)
		else:
			strategies = (
				'find_matching_releaser_in_dz2_by_demozoo0_id',
				'find_matching_releaser_in_dz2_by_slengpung_id',
				'find_matching_releaser_in_dz2_by_name_and_releases',
				'find_matching_releaser_in_dz2_by_name_and_groups',
				'find_matching_releaser_in_dz2_by_name_and_members',
			)
		for strategy in strategies:
			results = getattr(self, strategy)(releaser_info)
			if not results:
				continue
			if len(results) > 1 and not loose:
				raise Exception(
					'Multiple matches found for [%s] %s using strategy %s: %s' %
					(releaser_info['id'], releaser_info['name'], strategy, [releaser.id for releaser in results])
				)
			#for result in results:
			#	print "(%s) %s => %s (by %s)" % (
			#		releaser_info['id'],
			#		releaser_info['name'],
			#		results[0],
			#		strategy
			#	)
			return results
		
		return []
	
	def find_or_create_releaser(self, releaser_info):
		matches = self.find_matching_releaser_in_dz2(releaser_info)
		if matches:
			releaser = matches[0]
			if not releaser.demozoo0_id:
				releaser.demozoo0_id = releaser_info['id']
			if not releaser.slengpung_user_id:
				releaser.slengpung_user_id = releaser_info['slengpung_id']
			if not releaser.zxdemo_id:
				releaser.zxdemo_id = releaser_info['zxdemo_id']
			releaser.save()
		else:
			releaser = Releaser(
				name = releaser_info['name'],
				is_group = (releaser_info['type'] == 'Group'),
				slengpung_user_id = releaser_info['slengpung_id'],
				demozoo0_id = releaser_info['id'],
				zxdemo_id = releaser_info['zxdemo_id'],
				updated_at = datetime.datetime.now(),
				data_source = 'dz0'
			)
			releaser.save()
		
		for nick_info in demozoo0.nicks_for_releaser(releaser_info['id']):
			nick = self.find_or_create_nick_for_releaser(releaser, nick_info)
			for name in demozoo0.names_for_nick(nick_info['id']):
				self.add_variant_for_nick(nick, name)
		
		return releaser
	
	def find_or_create_nick_for_releaser(self, releaser, nick_info):
		nicks = releaser.nicks.filter(variants__name__iexact = nick_info['name'])
		if len(nicks) > 1:
			raise Exception("Releaser %d has more than one nick with name %s" % (releaser.id, nick_info['name']))
		elif len(nicks) == 1:
			nick = nicks[0]
		else:
			nick = Nick(
				releaser = releaser,
				name = nick_info['name'],
				abbreviation = nick_info['abbreviation'] or ''
			)
			nick.save()
		
		if nick_info['abbreviation'] and not nick.abbreviation:
			nick.abbreviation = nick_info['abbreviation']
			nick.save()
		
		return nick
	
	def add_variant_for_nick(self, nick, name):
		if not nick.variants.filter(name__iexact = name):
			variant = NickVariant(nick = nick, name = name)
			variant.save()
	
	def import_memberships_with_log_events(self):
		self.import_memberships_from_queryset(demozoo0.memberships_with_log_events())
	
	def import_memberships_from_zxdemo(self):
		self.import_memberships_from_queryset(demozoo0.memberships_from_zxdemo())
	
	def import_subgroupages(self):
		self.import_memberships_from_queryset(demozoo0.subgroupages())
	
	def import_memberships_from_queryset(self, queryset):
		for membership in queryset:
			print "(%s) %s in (%s) %s" % (
				membership['member']['id'], membership['member']['name'],
				membership['group']['id'], membership['group']['name']
			)
			member = self.find_or_create_releaser(membership['member'])
			group = self.find_or_create_releaser(membership['group'])
			membership_matches = Membership.objects.filter(member__id = member.id, group__id = group.id)
			if membership_matches:
				for match in membership_matches:
					print "- already exists"
					if (not membership['is_current']) and match.is_current:
						print "UPDATED: is_current = %s on dz0, vs %s on dz2" % (membership['is_current'], match.is_current)
						match.is_current = False
						match.save()
			else:
				print "- adding"
				new_membership = Membership(
					member = member,
					group = group,
					is_current = membership['is_current'],
					data_source = 'dz0'
				)
				new_membership.save()
			sys.stdout.flush()
	
	def import_credits(self):
		for credit in demozoo0.credits():
			production = self.find_or_create_production(credit['production'])
			if not production:
				continue
			releaser = self.find_or_create_releaser(credit['releaser'])
			nick = self.find_or_create_nick_for_releaser(releaser, credit['nick'])
			
			existing_credits = production.credits.filter(nick = nick)
			if existing_credits and existing_credits[0].role == credit['role']:
				pass
			elif existing_credits:
				print u"WARNING: existing credit for %s on %s - skipping" % (nick, production)
			else:
				print u"adding credit for %s on %s - %s" % (nick, production, credit['role'])
				credit = Credit(
					production = production,
					nick = nick,
					role = credit['role'])
				credit.save()
			sys.stdout.flush()
	
	def import_zxdemo_productions(self):
		for production_info in demozoo0.productions_from_zxdemo():
			self.find_or_create_production(production_info)
			sys.stdout.flush()
	
	def import_productions_introduced_on_demozoo0(self):
		for production_info in demozoo0.productions_introduced_on_demozoo0():
			self.find_or_create_production(production_info)
			sys.stdout.flush()
	
	def handle_noargs(self, **options):
		import sys
		import codecs
		sys.stdout = codecs.getwriter('utf8')(sys.stdout)
		
		# pending approval from Pouet:
		# self.import_all_users()
		# self.import_all_party_series()
		# self.import_all_releasers()
		
		self.import_subgroupages()
		self.import_memberships_from_zxdemo()
		self.import_memberships_with_log_events()
		self.import_credits()
		self.import_productions_introduced_on_demozoo0()
		self.import_zxdemo_productions()
		
		#for info in demozoo0.all_productions():
		#	match = self.find_matching_production_in_dz2(info)
		#for info in demozoo0.releasers_with_members():
		#	match = self.find_matching_releaser_in_dz2(info)
