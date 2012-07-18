import os
from datetime import datetime

from django.db import models
from django.core.management import call_command

from djapian import Indexer, Field, space
from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Person, MultipleIndexerEntry

class IndexerUpdateTest(BaseIndexerTest, BaseTestCase):
    def test_database_exists(self):
        self.assert_(os.path.exists(Entry.indexer._db._path))

    def test_document_count(self):
        self.assertEqual(Entry.indexer.document_count(), 3)

class IndexCommandTest(BaseTestCase):
    def setUp(self):
        p = Person.objects.create(name="Alex")
        entry1 = Entry.objects.create(
            author=p,
            title="Test entry",
            text="Not large text field"
        )
        entry2 = Entry.objects.create(
            author=p,
            title="Another test entry",
            is_active=False
        )

        call_command("index", daemonize=False)

    def test_database(self):
        self.assertEqual(Entry.indexer.document_count(), 1)

class IndexCommandMultipleIndexersTest(BaseTestCase):
    def setUp(self):
        MultipleIndexerEntry.objects.create(
            title="Test entry",
            text="Not large text field which helps us to test Djapian"
        )

        call_command("index", daemonize=False)

    def tearDown(self):
        for indexer in space.get_indexers_for_model(MultipleIndexerEntry):
            indexer.clear()

    def test_create_multiple_indexers(self):
        for indexer in space.get_indexers_for_model(MultipleIndexerEntry):
            self.assertEqual(indexer.document_count(), 1)
            self.assertEqual(indexer.search("test").count(), 1)

    def test_change_multiple_indexers(self):
        for entry in MultipleIndexerEntry.objects.all():
            entry.title = "Test entry: updated"
            entry.save()

        call_command("index", daemonize=False)

        self.assertEqual(MultipleIndexerEntry.indexer_title.search("updated").count(), 1)
        self.assertEqual(MultipleIndexerEntry.indexer_text.search("updated").count(), 0)

    def test_delete_multiple_indexers(self):
        MultipleIndexerEntry.objects.all().delete()

        call_command("index", daemonize=False)

        for indexer in space.get_indexers_for_model(MultipleIndexerEntry):
            self.assertEqual(indexer.document_count(), 0)
