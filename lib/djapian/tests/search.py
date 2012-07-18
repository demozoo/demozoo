from django.test import TestCase

from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Person, Comment
from djapian.indexer import CompositeIndexer
from djapian.tests.utils import WeightenedIndexerTest, WeightenedEntry

class IndexerSearchTextTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(IndexerSearchTextTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_result_count(self):
        self.assertEqual(len(self.result), 3)

    def test_result_row(self):
        self.assertEqual(self.result[0].instance, self.entries[0])

    def test_result_list(self):
        result = [r.instance for r in self.result]
        result.sort(key=lambda i: i.pk)

        expected = self.entries[0:3]
        expected.sort(key=lambda i: i.pk)

        self.assertEqual(result, expected)

    def test_score(self):
        self.assert_(self.result[0].percent in (99, 100))

    def test_hit_fields(self):
        hit = self.result[0]

        self.assertEqual(hit.tags['title'], 'Test entry')

    def test_best_match(self):
        self.assertEqual(self.result.best_match().instance.title, 'Test entry')

    def test_prefetch(self):
        result = self.result.prefetch()

        self.assertEqual(result[0].instance.author.name, 'Alex')

        result = self.result.prefetch(select_related=True)
        self.assert_(hasattr(result[0].instance, '_author_cache'))
        self.assertEqual(result[0].instance.author.name, 'Alex')

    def test_prefetch_deleted(self):
        result = self.result.prefetch()
        pk_val = self.result[0].pk

        Entry.objects.get(pk=pk_val).delete()

        self.assertTrue(len([str(r) for r in result]) > 0)

class AliasesTest(BaseTestCase):
    num_entries = 5

    def setUp(self):
        p = Person.objects.create(name="Alex")

        for i in range(self.num_entries):
            Entry.objects.create(author=p, title="Entry with number %s" % i, text="foobar " * i)

        Entry.indexer.update()

        self.result = Entry.indexer.search("subject:number")

    def test_result(self):
        self.assertEqual(len(self.result), self.num_entries)

class CorrectedQueryStringTest(BaseIndexerTest, BaseTestCase):
    def test_correction(self):
        results = Entry.indexer.search("texte").spell_correction()

        self.assertEqual(results.get_corrected_query_string(), "text")

class ParsedQueryTermsTest(BaseIndexerTest, BaseTestCase):
    def test_parsed_query(self):
        results = Entry.indexer.search("finding texts").stemming("en")

        self.assertEqual(list(results.get_parsed_query_terms()),
                         ["find", "text"])

class HighlightTest(BaseIndexerTest, BaseTestCase):
    TEXT = "Another not useful text message for tests"
    EXPECTED_RESULT = "Another not useful <strong>text</strong> message <strong>for</strong> tests"

    def test_highlight_clear_text(self):
        results = Entry.indexer.search("text for")

        self.assertEqual(results.highlight(self.TEXT), self.EXPECTED_RESULT)

    def test_highlight_stemming(self):
        results = Entry.indexer.search("texts for").stemming("en")

        self.assertEqual(results.highlight(self.TEXT), self.EXPECTED_RESULT)

class CompositeIndexerTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(CompositeIndexerTest, self).setUp()
        class StemNothingCompositeIndexer(CompositeIndexer):
            def _get_stem_language(self, obj=None):
                return 'none'
        self.indexer = StemNothingCompositeIndexer(Entry.indexer, Comment.indexer)

    def test_search(self):
        results = self.indexer.search('entry')

        self.assertEqual(len(results), 4) # 3 entries + 1 comment

    def test_sets_not_empty(self):
        results = self.indexer.search('entry')

        self.assertTrue(len(results[0].tags) > 0)

class OrderingTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(OrderingTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_order_by(self):
        entries = [e  for e in self.entries if e.is_active]
        entries.sort(key=lambda e: e.rating)

        self.assertEqual(
            list([r.instance for r in self.result.order_by('rating').prefetch()]),
            entries
        )

    def test_order_by_reversed(self):
        entries = [e  for e in self.entries if e.is_active]
        entries.sort(key=lambda e: e.rating)

        self.assertEqual(
            list([r.instance for r in self.result.order_by('-rating').prefetch()]),
            entries[::-1]
        )

class ResultSetTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(ResultSetTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test__get_item__1(self):
        result = self.result._clone()
        self.assertEqual(result[0].instance.author.name, 'Alex')

    def test__get_item__2(self):
        result = self.result._clone()
        self.assertEqual(result[1].instance.author.name, 'Alex')

    def test__get_item__3(self):
        result = self.result._clone()
        def test_f():
            try:
                res = result[-1]
            except AssertionError:
                self.fail("AssertionError has been raised instead of IndexError")
        self.assertRaises(IndexError, test_f)

class ResultSetInstancesTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(ResultSetInstancesTest, self).setUp()
        self.result = Entry.indexer.search("text")

    def test_instances__iter__(self):
        result = list(self.result.instances())
        result.sort(key=lambda i: i.pk)

        expected = self.entries[0:3]
        expected.sort(key=lambda i: i.pk)

        self.assertEqual(result, expected)

    def test_instances__get_item__1(self):
        result = self.result.instances()
        self.assertEqual(result[0].author.name, 'Alex')

class FlagsTest(BaseIndexerTest, BaseTestCase):
    def setUp(self):
        super(FlagsTest, self).setUp()

        self.result = Entry.indexer.search('mess').flags(
            Entry.indexer.flags.PARTIAL
        )

    def test_result(self):
        self.assertEqual(len(self.result), 2)

class WeightenedSearchTest(WeightenedIndexerTest, BaseTestCase):
    def setUp(self):
        super(WeightenedSearchTest, self).setUp()
        self.result = WeightenedEntry.indexer.search("entry")

    def test_highest_rating_item_is_on_top(self):
        self.assertEqual(self.result[0].instance.title.split()[0].lower(), 'third')
