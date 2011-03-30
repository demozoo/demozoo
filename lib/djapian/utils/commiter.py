class Commiter(object):
    def __init__(self, begin, commit, cancel):
        self._begin = begin
        self._commit = commit
        self._cancel = cancel

    def begin_page(self):
        pass

    def begin_object(self):
        pass

    def commit_page(self):
        pass

    def commit_object(self):
        pass

    def cancel_page(self):
        pass

    def cancel_object(self):
        pass

    @classmethod
    def create(cls, commit_each):
        class _ConcreteCommiter(cls):
            pass

        prefix = commit_each and 'object' or 'page'

        for name in ('begin', 'commit', 'cancel'):
            def make_method(name):
                return lambda self: getattr(self, '_%s' % name)()

            setattr(
                _ConcreteCommiter,
                '%s_%s' % (name, prefix),
                lambda self: make_method(name)
            )

        return _ConcreteCommiter
