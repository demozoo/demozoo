from demoscene.models import Releaser, Nick

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
		
		print "done."
