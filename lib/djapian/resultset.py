import xapian
import operator
from copy import deepcopy
from itertools import imap

from django.db.models import get_model
from django.utils.encoding import force_unicode

from djapian import utils, decider
from djapian.utils.decorators import retry_if_except

class ResultSet(object):
    def __init__(self, indexer, query_str, offset=0, limit=None,
                 order_by=None, prefetch=False, flags=None, stemming_lang=None,
                 filter=None, exclude=None, prefetch_select_related=False,
                 collapse_by=None, instances=False, stopper=None):
        self._indexer = indexer
        self._query_str = query_str
        self._offset = offset
        self._limit = limit
        self._order_by = order_by
        self._collapse_by = collapse_by
        self._prefetch = prefetch
        self._prefetch_select_related = prefetch_select_related
        self._instances = instances
        self._filter = filter or decider.X()
        self._exclude = exclude or decider.X()

        if flags is None:
            flags = xapian.QueryParser.FLAG_PHRASE\
                        | xapian.QueryParser.FLAG_BOOLEAN\
                        | xapian.QueryParser.FLAG_LOVEHATE
        self._flags = flags
        self._stemming_lang = stemming_lang
        self._stopper = stopper

        self._resultset_cache = None
        self._mset = None
        self._query = None
        self._query_parser = None

    # Public methods that produce another ResultSet

    def all(self):
        return self._clone()

    def spell_correction(self):
        return self._clone(
            flags=self._flags | xapian.QueryParser.FLAG_SPELLING_CORRECTION\
                                | xapian.QueryParser.FLAG_WILDCARD
        )

    def prefetch(self, select_related=False):
        return self._clone(
            prefetch=True,
            prefetch_select_related=select_related
        )

    def instances(self):
        return self._clone(instances=True)

    def order_by(self, field, relevance_first=False):
        return self._clone(order_by=(field, relevance_first))

    def flags(self, flags):
        return self._clone(flags=flags)

    def stemming(self, lang):
        return self._clone(stemming_lang=lang)

    def stopper(self, stopper):
        return self._clone(stopper=stopper)

    def count(self):
        return self._clone()._do_count()

    def get_corrected_query_string(self):
        self._get_mset()
        return self._query_parser.get_corrected_query_string()

    def filter(self, *fields, **raw_fields):
        clone = self._clone()
        clone._add_filter_fields(fields, raw_fields)
        return clone

    def exclude(self, *fields, **raw_fields):
        clone = self._clone()
        clone._add_exclude_fields(fields, raw_fields)
        return clone

    def best_match(self):
        return self._clone()[0]

    def collapse_by(self, field):
        return self._clone(collapse_by=field)

    def get_parsed_query_terms(self):
        clone = self._clone(stopper=None) # should not drop stop-words here
        query_parser = clone._indexer._get_query_parser(
            self._stemming_lang,
            self._stopper,
        )
        query_parser.set_stemming_strategy(xapian.QueryParser.STEM_ALL)
        return query_parser.parse_query(clone._query_str)

    def highlight(self, text, tag="strong"):
        terms = tuple(self.get_parsed_query_terms())
        if self._stemming_lang:
            stem = self._indexer.get_stemmer(self._stemming_lang)
        else:
            stem = lambda a: a
        # FIXME: should we support older Python versions without built-in `set' type?
        for word in set(text.split()):
            if stem(word.lower()) in terms:
                args = {"tag": tag, "word": word}
                text = text.replace(word, '<%(tag)s>%(word)s</%(tag)s>' % args)
        return text

    # Private methods

    def _prepare_fields(self, fields=None, raw_fields=None):
        fields = fields and reduce(operator.and_, fields) or decider.X()

        if raw_fields:
            fields = fields & reduce(
                operator.and_,
                map(
                    lambda value: decider.X(**{value[0]: value[1]}),
                    raw_fields.iteritems()
                )
            )
        self._check_fields(fields)
        return fields

    def _add_filter_fields(self, fields=None, raw_fields=None):
        self._filter &= self._prepare_fields(fields, raw_fields)

    def _add_exclude_fields(self, fields=None, raw_fields=None):
        self._exclude &= self._prepare_fields(fields, raw_fields)

    def _check_fields(self, fields):
        known_fields = set([f.prefix for f in self._indexer.tags])

        for field in fields.children:
            if isinstance(field, decider.X):
                self._check_fields(field)
            else:
                if field[0].split('__', 1)[0] not in known_fields:
                    raise ValueError("Unknown field '%s'" % field[0])

    def _clone(self, **kwargs):
        data = {
            "indexer": self._indexer,
            "query_str": self._query_str,
            "offset": self._offset,
            "limit": self._limit,
            "order_by": self._order_by,
            "collapse_by": self._collapse_by,
            "prefetch": self._prefetch,
            "instances": self._instances,
            "prefetch_select_related": self._prefetch_select_related,
            "flags": self._flags,
            "stemming_lang": self._stemming_lang,
            "stopper": self._stopper,
            "filter": deepcopy(self._filter),
            "exclude": deepcopy(self._exclude),
        }
        data.update(kwargs)

        return ResultSet(**data)

    def _do_count(self):
        self._get_mset()

        return self._mset.size()

    def _do_prefetch(self):
        model_map = {}

        for hit in self._resultset_cache:
            model_map.setdefault(hit.model, []).append(hit)

        for model, hits in model_map.iteritems():
            pks = [hit.pk for hit in hits]

            instances = model._default_manager.all()

            if self._prefetch_select_related:
                instances = instances.select_related()

            instances = instances.in_bulk(pks)

            for hit in hits:
                # check if the record has been deleted since the last Xapian index update
                instance = instances.get(hit.pk, None)
                if instance:
                    hit.instance = instance

        # filter results which may have become invalid during the search
        self._resultset_cache = filter(lambda hit: hit._instance, self._resultset_cache)

    def _get_mset(self):
        if self._mset is None:
            self._mset, self._query, self._query_parser = self._indexer._do_search(
                self._query_str,
                self._offset,
                self._limit,
                self._order_by,
                self._flags,
                self._stemming_lang,
                self._filter,
                self._exclude,
                self._collapse_by,
                self._stopper,
            )

    def _fetch_results(self):
        if self._resultset_cache is None:
            # self._parse_results() may raise DatabaseModifiedError exception,
            # thus we have to repeat retrieving of the whole MSet again
            retry_if_except(xapian.DatabaseModifiedError)(
                lambda: (self._get_mset(), self._parse_results()))()

        return self._resultset_cache

    def _parse_results(self):
        self._resultset_cache = []

        for match in self._mset:
            doc = match.document

            model = doc.get_value(2)
            model = get_model(*model.split('.'))
            pk = model._meta.pk.to_python(doc.get_value(1))

            percent = match.percent
            rank = match.rank
            weight = match.weight
            collapse_count = match.collapse_count or None
            collapse_key = match.collapse_key or None

            # check if the current indexer is CompositeIndexer
            if hasattr(self._indexer, '_indexers'):
                # so we must collect tags from every indexer of the model
                tags = []
                for indexer in self._indexer._indexers:
                    if indexer._model == model:
                        tags.extend(indexer.tags)
            else:
                tags = self._indexer.tags
            # get tags' values
            tags = dict([(tag.prefix, tag.extract(doc)) for tag in tags])

            self._resultset_cache.append(
                Hit(pk, model, percent, rank, weight, tags, collapse_count, collapse_key)
            )

        if self._prefetch:
            self._do_prefetch()

    def __iter__(self):
        self._fetch_results()
        if self._instances:
            return imap(lambda hit: hit.instance, self._resultset_cache)
        return iter(self._resultset_cache)

    def __len__(self):
        self._fetch_results()
        return len(self._resultset_cache)

    def __getitem__(self, k):
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        if not ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))):
            raise IndexError("Negative indexing is not supported.")

        if self._resultset_cache is not None:
            hit = self._fetch_results()[k]
            return self._instances and hit.instance or hit
        else:
            if isinstance(k, slice):
                start, stop = k.start, k.stop
                if start is None:
                    start = 0
                if stop is None:
                    limit = None
                else:
                    limit = stop - start

                return self._clone(offset=start, limit=limit)
            else:
                return iter(self._clone(offset=k, limit=1)).next()

    def __unicode__(self):
        return u"<ResultSet: query=%s>" % force_unicode(self._query_str)

class Hit(object):
    def __init__(self, pk, model, percent, rank, weight, tags, collapse_count, collapse_key):
        self.pk = pk
        self.model = model
        self.percent = percent
        self.rank = rank
        self.weight = weight
        self.tags = tags
        self.collapse_count = collapse_count
        self.collapse_key = collapse_key
        self._instance = None

    def get_instance(self):
        if self._instance is None:
            self._instance = self.model._default_manager.get(pk=self.pk)
        return self._instance

    def set_instance(self, instance):
        self._instance = instance

    instance = property(get_instance, set_instance)

    def __repr__(self):
        return "<Hit: model=%s pk=%s, percent=%s rank=%s weight=%s>" % (
            utils.model_name(self.model), self.pk, self.percent, self.rank, self.weight
        )
