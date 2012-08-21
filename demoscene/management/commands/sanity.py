from demoscene.models import Releaser, Nick, NickVariant

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction


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

		transaction.commit_unless_managed()

		print "done."
