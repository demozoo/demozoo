import sys
import cmd

from django.core.management.base import BaseCommand
from django.utils.text import smart_split

from djapian import utils
from djapian import IndexSpace

def with_index(func):
    def _decorator(cmd, arg):
        if cmd._current_index is None:
            print "No index selected"
            return

        return func(cmd, arg)
    _decorator.__doc__ = func.__doc__
    return _decorator

def split_arg(func):
    def _decorator(cmd, arg):
        bits = list(smart_split(arg))

        return func(cmd, *bits)
    _decorator.__doc__ = func.__doc__
    return _decorator

class Interpreter(cmd.Cmd):
    prompt = ">>> "

    def __init__(self, *args):
        self._current_index = None
        self._current_index_path = [None, None, None]

        if len(args):
            self.do_use(args[0])

        cmd.Cmd.__init__(self)

    def do_list(self, arg):
        """
        Lists all available indexes with their ids
        """
        print "Installed spaces/models/indexers:"

        def _is_selected(space, model=None, index=None):
            selected = [b for b in (space, model, index) if b is not None]
            return len(
                [1 for c, s in zip(self._current_index_path, selected) if c == s]
            ) == len(selected)

        for space_i, space in enumerate(IndexSpace.instances):
            print (_is_selected(space_i) and '* ' or '- ') + '%s: `%s`' % (space_i, space)
            for model_indexer_i, pair in enumerate(space.get_indexers().items()):
                model, indexers = pair
                print (_is_selected(space_i, model_indexer_i) and '  * ' or '  - ') +\
                        "%s.%s: `%s`" % (space_i, model_indexer_i, utils.model_name(model))
                for indexer_i, indexer in enumerate(indexers):
                    print (_is_selected(space_i, model_indexer_i, indexer_i) and '    * ' or '    - ') +\
                        "%s.%s.%s: `%s`" % (space_i, model_indexer_i, indexer_i, indexer)

    def do_exit(self, arg):
        """
        Exit shell
        """
        return True

    def do_use(self, index):
        """
        Changes current index
        """
        space, model, indexer, path = self._get_indexer(index)

        if indexer is not None:
            self._current_index = indexer
            self._current_index_path = path

            print "Using `%s:%s:%s` index." % (space, utils.model_name(model), indexer)

    def do_usecomposite(self, indexes):
        """
        Changes current index to composition of given indexers
        """
        from djapian.indexer import CompositeIndexer

        indexers = []
        for index in indexes.split(' '):
            indexers.append(self._get_indexer(index.strip()))

        self._current_index = CompositeIndexer(*[i[2] for i in indexers])

        print "Using composition of:"
        for indexer in indexers:
            space, model, indexer = indexer
            print "  `%s:%s:%s`" % (space, utils.model_name(model), indexer)
        print "indexes."

    @with_index
    @split_arg
    def do_query(self, query, _slice=''):
        """
        Returns objects fetched by given query
        """
        try:
            _slice = self._parse_slice(_slice)
        except ValueError:
            print 'Error: second argument must be slice'
            return

        print list(self._current_index.search(query)[_slice])

    @with_index
    def do_count(self, query):
        """
        Returns count of objects fetched by given query
        """
        print self._current_index.search(query).count()

    @with_index
    def do_total(self, arg):
        """
        Returns count of objects in index
        """
        print self._current_index.document_count()

    def do_stats(self, arg):
        """
        Print index status information
        """
        import operator
        print "Number of spaces: %s" % len(IndexSpace.instances)
        print "Number of indexes: %s" % reduce(
            operator.add,
            [len(space.get_indexers()) for space in IndexSpace.instances]
        )

    @with_index
    def do_docslist(self, slice=""):
        """
        Returns count of objects in index
        """
        db = self._current_index._db.open()

        _slice = self._parse_slice(slice, default=(1, db.get_lastdocid()))

        for i in range(_slice.start, _slice.stop + 1):
            doc = db.get_document(i)
            print "doc #%s:\n\tValues (%s):" % (i, doc.values_count())
            val = doc.values_begin()

            for i in range(doc.values_count()):
                print "\t\t%s: %s" % (val.get_valueno(), val.get_value())
                val.next()

            print "\tTerms (%s):" % doc.termlist_count()
            termlist = doc.termlist_begin()

            for i in range(doc.termlist_count()):
                print termlist.get_term(),
                termlist.next()
            print "\n"

    @with_index
    def do_delete(self, id):
        """
        Removes document by id
        """
        id = int(id)

        db = self._current_index._db.open(write=True)
        db.delete_document(id)
        print "Document #%s deleted." % id

    def _get_indexer(self, index):
        try:
            _space, _model, _indexer = map(int, index.split('.'))

            space = IndexSpace.instances[_space]
            model = space.get_indexers().keys()[_model]
            indexer = space.get_indexers()[model][_indexer]
        except (TypeError, IndexError, KeyError, ValueError):
            print 'Error: illegal index alias `%s`. See `list` command for available aliases' % index
            return None, None, None, None

        return space, model, indexer, [_space, _model, _indexer]

    def _parse_slice(self, _slice, delimeter=':', default=None):
        bits = map(int, [b for b in _slice.split(delimeter, 2) if b]) or default
        if not bits:
            return slice(None)
        elif len(bits) == 1:
            return slice(bits[0], bits[0] + 1)
        else:
            return slice(*bits)

        return bits

class Command(BaseCommand):
    help = "Djapian shell that provides capabilities to monitoring indexes."
    args = '[index_id]'

    requires_model_validation = True

    def handle(self, *args, **options):
        utils.load_indexes()

        try:
            Interpreter(*args).cmdloop("Interactive Djapian shell.")
        except KeyboardInterrupt:
            print "\n"
