import os
from datetime import datetime, timedelta

from django.db import models
from django.test import TestCase

import xapian
import djapian

class Person(models.Model):
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "djapian"

class Entry(models.Model):
    title = models.CharField(max_length=250, primary_key=True)

    author = models.ForeignKey(Person, related_name="entries")
    tags = models.CharField(max_length=250, null=True)
    created_on = models.DateTimeField(default=datetime.now)
    rating = models.FloatField(null=True)

    asset_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    text = models.TextField()

    editors = models.ManyToManyField(Person, related_name="edited_entries")

    def headline(self):
        return "%s - %s" % (self.author, self.title)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = "djapian"

class Comment(models.Model):
    entry = models.ForeignKey(Entry)

    author = models.ForeignKey(Person)
    text = models.TextField()

    class Meta:
        app_label = "djapian"

class EntryIndexer(djapian.Indexer):
    fields = ["text"]
    tags = [
        ("author", "author.name"),
        ("author_id", "author.id"),
        ("title", "title", 3),
        ("tag", "tags", 2),
        ("date", "created_on"),
        ("active", "is_active"),
        ("count", "asset_count"),
        ("editors", "editors"),
        ('rating', 'rating'),
    ]
    aliases = {
        "title": "subject",
        "author": "user",
    }
    trigger = lambda indexer, obj: obj.is_active
    def _get_stem_language(self, obj=None):
        return 'none'

class CommentIndexer(djapian.Indexer):
    fields = ['text']
    tags = [
        ('author', 'author.name')
    ]
    def _get_stem_language(self, obj=None):
        return 'none'

djapian.add_index(Entry, EntryIndexer, attach_as='indexer')
djapian.add_index(Comment, CommentIndexer, attach_as='indexer')

class BaseTestCase(TestCase):
    def tearDown(self):
        Entry.indexer.clear()
        Comment.indexer.clear()

class BaseIndexerTest(object):
    def setUp(self):
        self.person = Person.objects.create(name="Alex")

        self.entries = [
            Entry.objects.create(
                author=self.person,
                title="Test entry",
                rating=4.5,
                text="Not large text field wich helps us to test Djapian"
            ),
            Entry.objects.create(
                author=self.person,
                title="Another test entry - second",
                rating=3.6,
                text="Another not useful text message for tests",
                asset_count=5,
                created_on=datetime.now()-timedelta(hours=4)
            ),
            Entry.objects.create(
                author=self.person,
                title="Third entry for testing",
                rating=4.65,
                text="Third message text",
                asset_count=7,
                created_on=datetime.now()-timedelta(hours=2)
            ),
            Entry.objects.create(
                author=self.person,
                title="Innactive entry",
                is_active=False,
                text="Text wich will not be indexed"
            )
        ]

        Entry.indexer.update()

        self.comments =[
            Comment.objects.create(
                entry=self.entries[0],
                author=self.person,
                text='Hey, I comment my own entry!'
            )
        ]

        Comment.indexer.update()

class WeightenedEntry(models.Model):
    title = models.CharField(max_length=250, primary_key=True)

    created_on = models.DateTimeField(default=datetime.now)
    rating = models.FloatField(null=True)

    num_payments = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title

    def get_weight_int(self):
        return self.num_payments or 1

    class Meta:
        app_label = "djapian"

class WeightenedEntryIndexer(djapian.Indexer):
    fields = ["rating"]
    tags = [
        ("title", "title"),
        ("date", "created_on"),
        ("payments", "num_payments"),
        ("active", "is_active"),
    ]
    aliases = {
        "title": "subject",
    }
    trigger = lambda indexer, obj: obj.is_active
    weight = 'get_weight_int'

djapian.add_index(WeightenedEntry, WeightenedEntryIndexer, attach_as='indexer')

class WeightenedIndexerTest(BaseIndexerTest):
    def setUp(self):
        super(WeightenedIndexerTest, self).setUp()

        self.weightened_entries = [
            WeightenedEntry.objects.create(
                title="Test entry",
                rating=0.5,
            ),
            WeightenedEntry.objects.create(
                title="Another test entry - second",
                rating=2.6,
                num_payments=2,
                created_on=datetime.now()-timedelta(weeks=4)
            ),
            WeightenedEntry.objects.create(
                title="Third entry for testing",
                rating=4.65,
                num_payments=7,
                created_on=datetime.now()-timedelta(weeks=2)
            ),
            WeightenedEntry.objects.create(
                title="Innactive entry",
                is_active=False,
            )
        ]

        WeightenedEntry.indexer.update()

class StemEntry(models.Model):
    title = models.CharField(max_length=250, primary_key=True)
    text = models.TextField()

    class Meta:
        app_label = "djapian"

class MyStemImplementation(xapian.StemImplementation):
    def __call__(self, term):
        return term.lstrip()[:3]

class MyStem(xapian.Stem):
    def __init__(self, *args):
        super(MyStem, self).__init__(MyStemImplementation())

class StemEntryIndexer(djapian.Indexer):
    fields = ["title", "text"]
    stemmer_class = MyStem

    def get_stopper(self, lang=None):
        import xapian
        stopper = xapian.SimpleStopper()
        for stop_word in "the a an in at on for to".split():
            stopper.add(stop_word)
        return stopper

djapian.add_index(StemEntry, StemEntryIndexer, attach_as='indexer')

class StemIndexerTest(BaseIndexerTest):
    def setUp(self):
        super(StemIndexerTest, self).setUp()

        self.stopper = StemEntry.indexer.get_stopper("en")

        self.stem_entries = [
            StemEntry.objects.create(
                title="Test entry",
                text="Not large text field wich helps us to test Djapian"
            ),
            StemEntry.objects.create(
                title="Another test entry - second",
                text="Another not useful text message for tests",
            ),
            StemEntry.objects.create(
                title="Third entry for testing",
                text="Third message text",
            ),
        ]

        StemEntry.indexer.update()

class MultipleIndexerEntry(models.Model):
    title = models.CharField(max_length=250, primary_key=True)
    text = models.TextField()

    class Meta:
        app_label = "djapian"

class MultipleIndexerEntryTitleIndexer(djapian.Indexer):
    fields = ["title"]

class MultipleIndexerEntryTextIndexer(djapian.Indexer):
    fields = ["text"]

djapian.add_index(MultipleIndexerEntry, MultipleIndexerEntryTitleIndexer, attach_as='indexer_title')
djapian.add_index(MultipleIndexerEntry, MultipleIndexerEntryTextIndexer, attach_as='indexer_text')
