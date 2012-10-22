from django.test import TestCase

from djapian.tests.utils import BaseTestCase, StemIndexerTest, StemEntry, Entry

class IndexerStemTest(StemIndexerTest, BaseTestCase):
    def test_stemmer_class(self):
        stemmer = StemEntry.indexer.get_stemmer("en")
        self.assertEqual(stemmer("a"), "a")
        self.assertEqual(stemmer("foo"), "foo")
        self.assertEqual(stemmer("food"), "foo")

# We cannot test indexed search with a custom stemmer until Xapian will support it.

class IndexerStopWordsTest(StemIndexerTest, BaseTestCase):
    def test_stopper_class(self):
        self.assertEqual(self.stopper("a"), True)
        self.assertEqual(self.stopper("the"), True)
        self.assertEqual(self.stopper("then"), False)

    def test_stopper_result_set_untouched(self):
        result = Entry.indexer.search("the text")
        self.assertEqual(len(result), 0)

    def test_stopper_result_set_clean_index(self):
        result = StemEntry.indexer.search("text")
        self.assertEqual(len(result), 3)

    def test_stopper_result_set_clean_query(self):
        result = StemEntry.indexer.search("the text").stopper(self.stopper)
        self.assertEqual(len(result), 3)
