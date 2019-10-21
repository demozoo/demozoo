from __future__ import absolute_import, unicode_literals

import datetime
import unittest

from django.conf import settings
from django.test import TestCase

from zxdemo.models import Article, NewsItem


@unittest.skipIf(settings.ROOT_URLCONF != 'zxdemo.urls', "not running zxdemo environment")
class TestArticleModel(TestCase):
    def test_string_representation(self):
        article = Article.objects.create(
            zxdemo_id=99, created_at=datetime.datetime.now(), title="An article",
            summary="it's going to be good", content="oh actually it wasn't"
        )
        self.assertEqual("An article", str(article))


@unittest.skipIf(settings.ROOT_URLCONF != 'zxdemo.urls', "not running zxdemo environment")
class TestNewsItemModel(TestCase):
    def test_string_representation(self):
        news = NewsItem.objects.create(
            title="This is a headline",
            body="god I wish it wasn't",
            created_at=datetime.datetime.now()
        )
        self.assertEqual("This is a headline", str(news))
