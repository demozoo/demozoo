from django.core.management.base import NoArgsCommand
from django.core.management import call_command

from django.db import connection, transaction

class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		cursor = connection.cursor()
		cursor.execute("DELETE FROM djapian_change")
		transaction.commit_unless_managed()
		call_command('index', rebuild_index = True)
