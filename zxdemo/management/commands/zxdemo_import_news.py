from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from zxdemo.models import NewsItem
import pymysql


class Command(NoArgsCommand):

	def handle_noargs(self, **options):
		gasman = User.objects.get(username='gasman')
		NewsItem.objects.all().delete()

		connection = pymysql.connect(user="root", db="zxdemo")
		cur = connection.cursor()
		cur.execute("SELECT title, article, articledate FROM editorial")
		for row in cur:
			title, article, articledate = row
			NewsItem.objects.create(title=title, body=article, created_at=articledate, author=gasman)
