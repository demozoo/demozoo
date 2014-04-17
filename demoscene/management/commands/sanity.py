from demoscene.models import Releaser, Nick, NickVariant
from parties.models import Competition, ResultsFile
# from sceneorg.models import Directory
from taggit.models import Tag

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction
from django.db.models import Count


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		print "Looking for releasers without their name as a Nick"

		releasers = Releaser.objects.raw('''
			SELECT demoscene_releaser.*
			FROM
				demoscene_releaser
				LEFT JOIN demoscene_nick ON (
					demoscene_releaser.id = demoscene_nick.releaser_id
					AND demoscene_releaser.name = demoscene_nick.name
				)
			WHERE
				demoscene_nick.id IS NULL
		''')
		for releaser in releasers:
			print "creating nick for %s" % releaser
			nick = Nick(releaser=releaser, name=releaser.name)
			nick.save()

		print "Looking for Nicks without their name as a NickVariant"

		nicks = Nick.objects.raw('''
			SELECT demoscene_nick.*
			FROM
				demoscene_nick
				LEFT JOIN demoscene_nickvariant ON (
					demoscene_nick.id = demoscene_nickvariant.nick_id
					AND demoscene_nick.name = demoscene_nickvariant.name
				)
			WHERE
				demoscene_nickvariant.id IS NULL
		''')
		for nick in nicks:
			print "creating nick_variant for %s" % nick
			nick_variant = NickVariant(nick=nick, name=nick.name)
			nick_variant.save()

		print "Removing releaser abbreviations that are the same as the actual name"
		cursor = connection.cursor()
		cursor.execute('''
			UPDATE demoscene_nick
			SET abbreviation = ''
			WHERE LOWER(name) = LOWER(abbreviation)
		''')

		print "Looking for Nicks without their abbreviation as a NickVariant"

		nicks = Nick.objects.raw('''
			SELECT demoscene_nick.*
			FROM
				demoscene_nick
				LEFT JOIN demoscene_nickvariant ON (
					demoscene_nick.id = demoscene_nickvariant.nick_id
					AND demoscene_nick.abbreviation = demoscene_nickvariant.name
				)
			WHERE
				demoscene_nick.abbreviation <> ''
				AND demoscene_nickvariant.id IS NULL
		''')
		for nick in nicks:
			print "creating nick_variant for %s" % nick.abbreviation
			nick_variant = NickVariant(nick=nick, name=nick.abbreviation)
			nick_variant.save()

		print "Truncating fuzzy dates to first of the month / first of January"
		cursor = connection.cursor()
		cursor.execute('''
			UPDATE demoscene_production
			SET release_date_date = date_trunc('month', release_date_date)
			WHERE release_date_precision = 'm'
		''')
		cursor.execute('''
			UPDATE demoscene_production
			SET release_date_date = date_trunc('year', release_date_date)
			WHERE release_date_precision = 'y'
		''')

		print "Removing abbreviations on scener nicks"
		nicks = Nick.objects.exclude(abbreviation='').filter(releaser__is_group=False)
		for nick in nicks:
			print "Removing abbreviation %s of %s" % (nick.abbreviation, nick.name)
			nick.abbreviation = ''
			nick.save()

		print "Stripping leading / trailing spaces from names and titles"
		cursor.execute('''
			UPDATE demoscene_production
			SET title = REGEXP_REPLACE(title, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE title LIKE ' %%' OR title LIKE '%% '
		''')
		cursor.execute('''
			UPDATE demoscene_releaser
			SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE name LIKE ' %%' OR name LIKE '%% '
		''')
		cursor.execute('''
			UPDATE demoscene_nick
			SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE name LIKE ' %%' OR name LIKE '%% '
		''')
		cursor.execute('''
			UPDATE demoscene_nickvariant
			SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE name LIKE ' %%' OR name LIKE '%% '
		''')
		cursor.execute('''
			UPDATE parties_party
			SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE name LIKE ' %%' OR name LIKE '%% '
		''')
		cursor.execute('''
			UPDATE parties_partyseries
			SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
			WHERE name LIKE ' %%' OR name LIKE '%% '
		''')

		# skip this. it takes ages.
		# print "Recursively marking children of deleted scene.org dirs as deleted"
		# for dir in Directory.objects.filter(is_deleted=True):
		#	dir.mark_deleted()

		print "Converting invitation competitions to party invitation relations"
		invitation_compos = Competition.objects.filter(name__istartswith='invitation').select_related('party')
		for compo in invitation_compos:
			placings = compo.placings.select_related('production')

			is_real_compo = False
			for placing in placings:
				if placing.ranking != '' or placing.score != '':
					is_real_compo = True
				compo.party.invitations.add(placing.production)

			if not is_real_compo:
				compo.delete()

		print "Checking encodings on results files"
		results_files = ResultsFile.objects.all()
		for results_file in results_files:
			try:
				results_file.text
			except UnicodeDecodeError:
				print "Error on /parties/%d/results_file/%d/ - cannot decode as %r" % (results_file.party_id, results_file.id, results_file.encoding)
			except IOError:
				pass  # ignore files that aren't on disk (which probably means this is a local dev instance with a live db)

		print "Deleting unused tags"
		Tag.objects.annotate(num_prods=Count('taggit_taggeditem_items')).filter(num_prods=0).delete()

		transaction.commit_unless_managed()

		print "done."
