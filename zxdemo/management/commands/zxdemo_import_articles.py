from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from zxdemo.models import Article

import urllib2
from dateutil.parser import parse
from BeautifulSoup import BeautifulSoup


class Command(NoArgsCommand):

	def handle_noargs(self, **options):
		Article.objects.all().delete()

		req = urllib2.Request('http://zxdemo.org/api/articles.php')
		page = urllib2.urlopen(req)
		soup = BeautifulSoup(page, fromEncoding="ISO-8859-1", convertEntities=BeautifulSoup.HTML_ENTITIES)

		for article in soup.findAll('article'):
			id = int(article.find('id').string)
			title = unicode(article.find('title').string or '')
			summary = unicode(article.find('summary').string)
			content = unicode(article.find('content').string)
			created_at = parse(article.find('pubdate').text)

			Article.objects.create(title=title, summary=summary, content=content, created_at=created_at, zxdemo_id=id)
