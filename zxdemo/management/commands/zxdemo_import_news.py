from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from zxdemo.models import NewsItem

import urllib2
from dateutil.parser import parse
from BeautifulSoup import BeautifulSoup


class Command(NoArgsCommand):

	def handle_noargs(self, **options):
		gasman = User.objects.get(username='gasman')
		NewsItem.objects.all().delete()

		req = urllib2.Request('http://zxdemo.org/api/news.php')
		page = urllib2.urlopen(req)
		soup = BeautifulSoup(page, fromEncoding="ISO-8859-1", convertEntities=BeautifulSoup.HTML_ENTITIES)

		for news_item in soup.findAll('news_item'):
			title = news_item.find('title').string or ''
			body = news_item.find('article').string
			created_at = parse(news_item.find('date').text)

			NewsItem.objects.create(title=title, body=body, created_at=created_at, author=gasman)
