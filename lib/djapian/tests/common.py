import os

from djapian import Field
from djapian.tests.utils import BaseTestCase, BaseIndexerTest, Entry, Person
from djapian.models import Change
from django.utils.encoding import force_unicode

class IndexerTest(BaseTestCase):
    def test_fields_count(self):
        self.assertEqual(len(Entry.indexer.fields), 1)

    def test_tags_count(self):
        self.assertEqual(len(Entry.indexer.tags), 9)

class FieldResolverTest(BaseTestCase):
    def setUp(self):
        person = Person.objects.create(name="Alex", age=22)
        another_person = Person.objects.create(name="Sam", age=25)

        self.entry = Entry.objects.create(author=person, title="Test entry")
        self.entry.editors.add(person, another_person)

    def test_simple_attribute(self):
        self.assertEqual(Field("title", Entry).resolve(self.entry), "Test entry")

    def test_related_attribute(self):
        self.assertEqual(Field("author.name", Entry).resolve(self.entry), "Alex")

    def test_fk_attribute(self):
        self.assertEqual(force_unicode(Field("author", Entry).resolve(self.entry)), "Alex")

    def test_m2m_attribute(self):
        self.assertEqual(force_unicode(Field("editors", Entry).resolve(self.entry)), "Alex, Sam")

    def test_m2m_field_attribute(self):
        self.assertEqual(force_unicode(Field("editors.age", Entry).resolve(self.entry)), "22, 25")

    def test_method(self):
        self.assertEqual(
            Field("headline", Entry).resolve(self.entry),
            "Alex - Test entry"
        )

class ChangeTrackingTest(BaseTestCase):
    def setUp(self):
        p = Person.objects.create(name="Alex")
        Entry.objects.create(author=p, title="Test entry")
        Entry.objects.create(
            author=p,
            title="Another test entry",
            is_active=False
        )

    def test_change_count(self):
        self.assertEqual(Change.objects.count(), 2)

class ChangeTrackingUpdateTest(BaseTestCase):
    def setUp(self):
        p = Person.objects.create(name="Alex")
        entry = Entry.objects.create(author=p, title="Test entry")

        entry.text = "Foobar text"
        entry.save()

    def test_change_count(self):
        self.assertEqual(Change.objects.count(), 1)

    def test_change_action(self):
        self.assertEqual(Change.objects.get().action, "add")

class ChangeTrackingDeleteTest(BaseTestCase):
    def setUp(self):
        p = Person.objects.create(name="Alex")
        entry = Entry.objects.create(author=p, title="Test entry")
        entry.delete()

    def test_change_count(self):
        self.assertEqual(Change.objects.count(), 0)
