import xapian

def retry_if_except(errors, num_retry=4, cleanup_callback=None):
    def _wrap(func):
        def _inner(*args, **kwargs):
            for n in reversed(range(num_retry)):
                try:
                    return func(*args, **kwargs)
                except errors:
                    # propagate the exception if we have run out of tries
                    if not n:
                        raise
                    # perform a clean up action before the next attempt if required
                    if callable(cleanup_callback):
                        cleanup_callback()
        return _inner
    return _wrap

def reopen_if_modified(database, num_retry=3,
                   errors=xapian.DatabaseModifiedError):
    return retry_if_except(errors,
                           num_retry=num_retry,
                           cleanup_callback=lambda: database.reopen())
