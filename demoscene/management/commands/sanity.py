from demoscene.models import Releaser, Nick, NickVariant

from django.core.management.base import NoArgsCommand

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
			nick = Nick(releaser = releaser, name = releaser.name)
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
			nick_variant = NickVariant(nick = nick, name = nick.name)
			nick_variant.save()
		
		print "done."
