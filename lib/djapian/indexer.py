import datetime
import os

from django.db import models
from django.utils.itercompat import is_iterable
from djapian.signals import post_save, pre_delete
from django.conf import settings
from django.utils.encoding import smart_str

from djapian import decider
from djapian.database import CompositeDatabase
from djapian.resultset import ResultSet
from djapian.utils.paging import paginate
from djapian.utils.commiter import Commiter
from djapian.utils import DEFAULT_WEIGHT, model_name

import xapian

class Field(object):
    raw_types = (int, long, float, basestring, bool, models.Model,
                 datetime.time, datetime.date, datetime.datetime)

    def __init__(self, path, model, weight=DEFAULT_WEIGHT, prefix='', number=None):
        self.path = path
        self.weight = weight
        self.prefix = prefix
        self.number = number
        self.model = model

    def get_tag(self):
        return self.prefix.upper()

    def convert(self, field_value):
        """
        Generates index values (for sorting) for given field value and its content type
        """
        if field_value is None:
            return None

        content_type = self._get_content_type(field_value)

        value = field_value

        if self._is_float_or_interger(content_type):
            value = xapian.sortable_serialise(field_value)
        elif isinstance(content_type, (models.BooleanField, bool)):
            # Boolean fields are stored as 't' or 'f'
            value = field_value and 't' or 'f'
        elif isinstance(content_type, (models.DateTimeField, datetime.datetime)):
            # DateTime fields are stored as %Y%m%d%H%M%S (better sorting)
            value = field_value.strftime('%Y%m%d%H%M%S')

        return smart_str(value)

    def resolve_one(self, value, name):
        value = getattr(value, name)

        if isinstance(value, models.Manager):
            value = value.all()
        elif callable(value):
            value = value()

        return value

    def resolve(self, value):
        bits = self.path.split(".")

        for bit in bits:
            if is_iterable(value):
                value = ', '.join(
                    map(lambda v: smart_str(self.resolve_one(v, bit)), value)
                )
            else:
                value = self.resolve_one(value, bit)

        if isinstance(value, self.raw_types):
            return value
        if is_iterable(value):
            return ', '.join(map(smart_str, value))

        return value and smart_str(value) or None

    def extract(self, document):
        if self.number:
            value = document.get_value(self.number)

            content_type = self._get_content_type(value)

            if self._is_float_or_interger(content_type):
                value = xapian.sortable_unserialise(value)

            return value

        return None

    def _get_content_type(self, field_value):
        """Returns field's models.Field instance or value if such model field does not exist"""
        try:
            return self.model._meta.get_field(self.path.split('.', 1)[0])
        except models.FieldDoesNotExist:
            return field_value

    def _is_float_or_interger(self, content_type):
        return isinstance(content_type, (models.IntegerField, models.FloatField, int, long, float,))

class Indexer(object):
    field_class = Field
    decider = decider.CompositeDecider
    free_values_start_number = 11

    fields = []
    tags = []
    aliases = {}
    trigger = lambda indexer, obj: True
    stemming_lang_accessor = None
    stemmer_class = xapian.Stem
    stopper = None

    flags = type.__new__(
        type,
        'SearchFlags',
        (object,),
        dict([
            (name[5:], value)\
                for name, value in xapian.QueryParser.__dict__.iteritems()\
                    if name.startswith('FLAG_')
        ])
    )

    def __init__(self, db, model):
        """
        Initialize an Indexer whose index data to `db`.
        `model` is the Model whose instances will be used as documents.
        Note that fields from other models can still be used in the index,
        but this model will be the one returned from search results.
        """
        self._prepare(db, model)

        # Parse fields
        # For each field checks if it is a tuple or a list and add it's weight
        for field in self.__class__.fields:
            if isinstance(field, (tuple, list)):
                self.fields.append(self.field_class(field[0], self._model, field[1]))
            else:
                self.fields.append(self.field_class(field, self._model))

        # Parse prefixed fields
        valueno = self.free_values_start_number

        for field in self.__class__.tags:
            tag, path = field[:2]
            if len(field) == 3:
                weight = field[2]
            else:
                weight = DEFAULT_WEIGHT

            self.tags.append(self.field_class(path, self._model, weight, prefix=tag, number=valueno))
            valueno += 1

        for tag, aliases in self.__class__.aliases.iteritems():
            if self.has_tag(tag):
                if not isinstance(aliases, (list, tuple)):
                    aliases = (aliases,)
                self.aliases[tag] = aliases
            else:
                raise ValueError("Cannot create alias for tag `%s` that doesn't exist" % tag)

        models.signals.post_save.connect(post_save, sender=self._model)
        models.signals.pre_delete.connect(pre_delete, sender=self._model)

    def __unicode__(self):
        return self.__class__.get_descriptor()

    def __str__(self):
        return smart_str(self.__unicode__())

    def has_tag(self, name):
        return self.tag_index(name) is not None

    def tag_index(self, name):
        for field in self.tags:
            if field.prefix == name:
                return field.number

    def get_stemmer(self, stemming_lang):
        """
        Return a stemmer instance for the requested stemming language.
        """
        # Just returns a stemmer instance. We do not provide any optimization like
        # instance memoization here because the default stemmer is stateless.
        return self.stemmer_class(stemming_lang)

    def get_stopper(self, lang):
        """
        Return a stopper instance for the requested language.
        """
        # There are no default stop words lists bundled with Xapian.
        return self.stopper

    @classmethod
    def get_descriptor(cls):
        return ".".join([cls.__module__, cls.__name__]).lower()

    # Public Indexer interface

    def update(self, documents=None, after_index=None, per_page=10000, commit_each=False):
        """
        Update the database with the documents.
        There are some default value and terms in a document:
         * Values:
           1. Used to store the ID of the document
           2. Store the model of the object (in the string format, like
              "project.app.model")
           3. Store the indexer descriptor (module path)
           4..10. Free

         * Terms
           UID: Used to store the ID of the document, so we can replace
                the document by the ID
        """
        # Open Xapian Database
        database = self._db.open(write=True)

        # If doesnt have any document at all
        if documents is None:
            update_queue = self._model.objects.all()
        else:
            update_queue = documents

        commiter = Commiter.create(commit_each)(
            lambda: database.begin_transaction(flush=True),
            database.commit_transaction,
            database.cancel_transaction
        )

        # Get each document received
        for page in paginate(update_queue, per_page):
            try:
                commiter.begin_page()

                for obj in page.object_list:
                    commiter.begin_object()

                    try:
                        if not self.trigger(obj):
                            self.delete(obj.pk, database)
                            continue

                        doc = xapian.Document()

                        # Add default terms and values
                        uid = self._create_uid(obj)
                        doc.add_term(self._create_uid(obj))
                        self._insert_meta_values(doc, obj)

                        generator = xapian.TermGenerator()
                        generator.set_database(database)
                        generator.set_document(doc)
                        generator.set_flags(xapian.TermGenerator.FLAG_SPELLING)

                        stemming_lang = self._get_stem_language(obj)
                        if stemming_lang:
                            stemmer = self.get_stemmer(stemming_lang)
                            generator.set_stemmer(stemmer)

                            stopper = self.get_stopper(stemming_lang)
                            if stopper:
                                generator.set_stopper(stopper)

                        # Get a weight for the object
                        obj_weight = self._get_object_weight(obj)
                        # Index fields
                        self._do_index_fields(doc, generator, obj, obj_weight)

                        database.replace_document(uid, doc)
                        if after_index:
                            after_index(obj)

                        commiter.commit_object()
                    except Exception:
                        commiter.cancel_object()
                        raise

                commiter.commit_page()
            except Exception:
                commiter.cancel_page()
                raise

    def search(self, query):
        return ResultSet(self, query)

    def delete(self, obj, database=None):
        """
        Delete a document from index
        """
        try:
            if database is None:
                database = self._db.open(write=True)
            database.delete_document(self._create_uid(obj))
        except (IOError, RuntimeError, xapian.DocNotFoundError), e:
            pass

    def document_count(self):
        return self._db.document_count()

    __len__ = document_count

    def clear(self):
        self._db.clear()

    # Private Indexer interface

    def _prepare(self, db, model=None):
        """Initialize attributes"""
        self._db = db
        self._model = model
        self._model_name = model and model_name(model)

        self.fields = [] # Simple text fields
        self.tags = [] # Prefixed fields
        self.aliases = {}

    def _get_meta_values(self, obj):
        if isinstance(obj, models.Model):
            pk = obj.pk
        else:
            pk = obj
        return [pk, self._model_name, self.__class__.get_descriptor()]

    def _insert_meta_values(self, doc, obj, start=1):
        for value in self._get_meta_values(obj):
            doc.add_value(start, smart_str(value))
            start += 1
        return start

    def _create_uid(self, obj):
        """
        Generates document UID for given object
        """
        return "UID-" + "-".join(map(smart_str, self._get_meta_values(obj)))

    def _do_search(self, query, offset, limit, order_by, flags, stemming_lang,
                   filter, exclude, collapse_by, stopper):
        """
        flags are as defined in the Xapian API :
        http://www.xapian.org/docs/apidoc/html/classXapian_1_1QueryParser.html
        Combine multiple values with bitwise-or (|).
        """
        database = self._db.open()
        enquire = xapian.Enquire(database)

        if order_by is None or order_by[0] in (None, 'RELEVANCE'):
            enquire.set_sort_by_relevance()
        else:
            ascending = True
            order_by, relevance_first = order_by
            if order_by.startswith('-'):
                ascending = False

            if order_by[0] in '+-':
                order_by = order_by[1:]

            try:
                valueno = self.tag_index(order_by)
            except (ValueError, TypeError):
                raise ValueError("Field %s cannot be used in order_by clause"
                                 " because it doen't exist in index" % order_by)

            if relevance_first:
                enquire.set_sort_by_relevance_then_value(valueno, ascending)
            else:
                enquire.set_sort_by_value_then_relevance(valueno, ascending)

        if collapse_by:
            try:
                valueno = self.tag_index(collapse_by)
            except (ValueError, TypeError):
                raise ValueError("Field %s cannot be used in set_collapse_key"
                                 " because it doen't exist in index" % collapse_by)
            enquire.set_collapse_key(valueno)

        query, query_parser = self._parse_query(query, database, flags, stemming_lang, stopper)
        enquire.set_query(
            query
        )

        decider = self.decider(self._model, self.tags, filter, exclude)

        if limit is None:
            limit = self.document_count()

        return enquire.get_mset(
            offset,
            limit,
            None,
            decider
        ), query, query_parser

    def _get_stem_language(self, obj=None):
        """
        Returns stemming language for given object if acceptable or model wise
        """
        # Use the language defined in DJAPIAN_STEMMING_LANG
        language = getattr(settings, 'DJAPIAN_STEMMING_LANG', 'none')

        if language == 'multi':
            language = 'none'

            if obj:
                try:
                    language = self.field_class(
                        self.stemming_lang_accessor, self._model
                    ).resolve(obj)
                except AttributeError:
                    pass

        return language

    def _get_query_parser(self, stemming_lang, stopper=None):
        """
        Creates a Xapian QueryParser object and applies
        a stemmer, a stopper and prefixes for tags and aliases
        """
        query_parser = xapian.QueryParser()

        query_parser.set_default_op(xapian.Query.OP_AND)

        for field in self.tags:
            query_parser.add_prefix(field.prefix.lower(), field.get_tag())
            if field.prefix in self.aliases:
                for alias in self.aliases[field.prefix]:
                    query_parser.add_prefix(alias, field.get_tag())

        if stemming_lang in (None, "none"):
            stemming_lang = self._get_stem_language()

        if stemming_lang:
            stemmer = self.get_stemmer(stemming_lang)
            query_parser.set_stemmer(stemmer)
            query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

            if not stopper:
                stopper = self.get_stopper(stemming_lang)

        if stopper:
            query_parser.set_stopper(stopper)

        return query_parser

    def _parse_query(self, term, db, flags, stemming_lang, stopper=None):
        """
        Parses search queries
        """
        # Instance Xapian Query Parser
        query_parser = self._get_query_parser(stemming_lang, stopper)
        query_parser.set_database(db)

        parsed_query = query_parser.parse_query(term, flags)

        return parsed_query, query_parser

    def _get_object_weight(self, obj):
        """
        Returns a default weight value for the object. 
        """
        if hasattr(self.__class__, 'weight'):
            obj_weight = self.field_class(self.__class__.weight, self._model).resolve(obj)
        else:
            obj_weight = DEFAULT_WEIGHT
        return obj_weight

    def _do_index_fields(self, doc, generator, obj, obj_weight):
        """
        Indexes fields of the object.
        """
        for field in self.fields + self.tags:
            # Trying to resolve field value or skip it
            try:
                value = field.resolve(obj)
            except AttributeError:
                continue

            if value is None:
                continue

            if field.prefix:
                doc.add_value(field.number, field.convert(value))

            prefix = smart_str(field.get_tag())
            value = smart_str(value)
            generator.index_text(value, field.weight*obj_weight, prefix)
            if prefix:  # if prefixed then also index without prefix
                generator.index_text(value, field.weight*obj_weight)

class CompositeIndexer(Indexer):
    def __init__(self, *indexers):
        self._indexers = indexers
        self._prepare(
            db=CompositeDatabase([indexer._db for indexer in indexers])
        )

    def clear(self):
        raise NotImplementedError

    def update(self, *args):
        raise NotImplementedError

    def tag_index(self, name):
        return reduce(lambda a, b: a == b and a or None,
                      [indexer.tag_index(name) for indexer in self._indexers])
