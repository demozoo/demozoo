from django.test import TestCase

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Person
from djapian import X

class FilteringTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(FilteringTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_filter(self):
        self.assertEqual(self.result.filter(count=5).count(), 1)
        self.assertEqual(self.result.filter(count__lt=6).count(), 2)
        self.assertEqual(self.result.filter(count__gte=5).count(), 2)

        self.assertEqual(self.result.filter(count__in=[5, 7]).count(), 2)

        self.assertEqual(self.result.filter(rating__lte=4.5).count(), 2)

    def test_exclude(self):
        self.assertEqual(self.result.exclude(count=5).count(), 2)
        self.assertEqual(self.result.exclude(count__lt=6).count(), 1)
        self.assertEqual(self.result.exclude(count__gte=5).count(), 1)

    def test_filter_exclude(self):
        self.assertEqual(self.result.filter(count__lt=6).exclude(count=5).count(), 1)

    def test_complex(self):
        self.assertEqual(self.result.filter(X(count__lt=6) & ~X(count=5)).count(), 1)
        self.assertEqual(self.result.filter(X(count=7) | X(count=5)).count(), 2)

    def test_convert(self):
        self.assertEqual(self.result.filter(author_id=1).count(), 3)

class LookupTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(LookupTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_exact(self):
        self.assertEqual(self.result.filter(title__startswith='Test entry').count(), 1)
        self.assertEqual(self.result.filter(title__istartswith='test entry').count(), 1)

    def test_startswith(self):
        self.assertEqual(self.result.filter(title__startswith='Third').count(), 1)
        self.assertEqual(self.result.filter(title__istartswith='third').count(), 1)

    def test_endswith(self):
        self.assertEqual(self.result.filter(title__endswith='- second').count(), 1)
        self.assertEqual(self.result.filter(title__iendswith='- Second').count(), 1)

    def test_contains(self):
        self.assertEqual(self.result.filter(title__contains='for').count(), 1)
        self.assertEqual(self.result.filter(title__icontains='For').count(), 1)

    def test_regex(self):
        self.assertEqual(self.result.filter(title__regex=r'^Test[ \w]+$').count(), 1)
        self.assertEqual(self.result.filter(title__iregex=r'^test[ \w]+$').count(), 1)
