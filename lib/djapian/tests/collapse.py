from django.test import TestCase

from djapian import CompositeIndexer
from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Comment

class CollapseTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(CollapseTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_collapse(self):
        # all entries have the same author
        self.assertEqual(self.result.collapse_by("author").count(), 1)

    def test_result_hit_collapse_count(self):
        # we should have (number of all active objects - 1) objects been collapsed
        self.assertEqual(self.result.collapse_by("author")[0].collapse_count, Entry.objects.filter(is_active=True).count() - 1)

    def test_result_hit_collapse_key(self):
        self.assertEqual(self.result.collapse_by("author")[0].collapse_key, "Alex")

    def test_result_hit_collapse_count_is_none(self):
        # if collapse_by() has not been used both collapse_count and collapse_key should be None
        self.assertEqual(self.result[0].collapse_count, None)

    def test_result_hit_collapse_key_is_none(self):
        self.assertEqual(self.result[0].collapse_key, None)

    def test_collapse_composite(self):
        # all entries have the same author
        indexer = CompositeIndexer(Entry.indexer, Comment.indexer)
        self.assertEqual(indexer.search("test").collapse_by("author").count(), 1)
