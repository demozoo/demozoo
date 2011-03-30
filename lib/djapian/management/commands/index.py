from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django.utils.daemonize import become_daemon
from django.contrib.contenttypes.models import ContentType

import os
import sys
import operator
import time
from datetime import datetime
from optparse import make_option

from djapian.models import Change
from djapian import utils
from djapian.utils.paging import paginate
from djapian.utils.commiter import Commiter
from djapian import IndexSpace

def get_content_types(app_models, *actions):
    lookup_args = dict(action__in=actions)
    if app_models is not None:
        ct_list = [ContentType.objects.get_for_model(model) for model in app_models]
        lookup_args.update(dict(content_type__in=ct_list))
    types = Change.objects.filter(models.Q(**lookup_args))\
                    .values_list('content_type', flat=True)\
                    .distinct()
    return ContentType.objects.filter(pk__in=types)

def get_indexers(content_type):
    return reduce(
        operator.add,
        [space.get_indexers_for_model(content_type.model_class())
            for space in IndexSpace.instances]
    )

@transaction.commit_manually
def update_changes(verbose, timeout, once, per_page, commit_each, app_models=None):
    counter = [0]

    def reset_counter():
        counter[0] = 0

    def after_index(obj):
        counter[0] += 1

        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()

    commiter = Commiter.create(commit_each)(
        lambda: None,
        transaction.commit,
        transaction.rollback
    )

    while True:
        count = Change.objects.count()
        if count > 0 and verbose:
            print 'There are %d objects to update' % count

        for ct in get_content_types(app_models, 'add', 'edit'):
            indexers = get_indexers(ct)

            for page in paginate(
                            Change.objects.filter(content_type=ct, action__in=('add', 'edit'))\
                                .select_related('content_type')\
                                .order_by('object_id'),
                            per_page
                        ):# The objects must be sorted by date
                commiter.begin_page()

                try:
                    for indexer in indexers:
                        indexer.update(
                            ct.model_class()._default_manager.filter(
                                pk__in=[c.object_id for c in page.object_list]
                            ).order_by('pk'),
                            after_index,
                            per_page,
                            commit_each
                        )

                    for change in page.object_list:
                        change.delete()

                    commiter.commit_page()
                except Exception:
                    if commit_each:
                        for change in page.object_list[:counter[0]]:
                            change.delete()
                        commiter.commit_object()
                    else:
                        commiter.cancel_page()
                    raise

                reset_counter()

        for ct in get_content_types(app_models, 'delete'):
            indexers = get_indexers(ct)

            for change in Change.objects.filter(content_type=ct, action='delete'):
                for indexer in indexers:
                    indexer.delete(change.object_id)
                    change.delete()

        # If using transactions and running Djapian as a daemon, transactions
        # need to be committed on each iteration, otherwise Djapian will not
        # catch changes. We also need to use the commit_manually decorator.
        #
        # Background information:
        #
        # Autocommit is turned off by default according to PEP 249.
        # PEP 249 states "Database modules that do not support transactions
        #                 should implement this method with void functionality".
        # Consistent Nonlocking Reads (InnoDB):
        # http://dev.mysql.com/doc/refman/5.0/en/innodb-consistent-read-example.html
        transaction.commit()

        if once:
            break

        time.sleep(timeout)

def rebuild(verbose, per_page, commit_each, app_models=None):
    def after_index(obj):
        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()

    for space in IndexSpace.instances:
        for model, indexers in space.get_indexers().iteritems():
            if app_models is None or model in app_models:
                for indexer in indexers:
                    indexer.clear()
                    indexer.update(None, after_index, per_page, commit_each)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbose', dest='verbose', default=False,
                    action='store_true',
                    help='Verbosity output'),
        make_option('--daemonize', dest='make_daemon', default=False,
                    action='store_true',
                    help='Do not fork the process'),
        make_option('--loop', dest='loop', default=False,
                    action='store_true',
                    help='Run update loop indefinetely'),
        make_option('--time-out', dest='timeout', default=10,
                    action='store', type='int',
                    help='Time to sleep between each query to the'
                         ' database (default: %default)'),
        make_option('--rebuild', dest='rebuild_index', default=False,
                    action='store_true',
                    help='Rebuild index database'),
        make_option('--per_page', dest='per_page', default=1000,
                    action='store', type='int',
                    help='Working page size'),
        make_option('--commit_each', dest='commit_each', default=False,
                    action='store_true',
                    help='Commit/flush changes on every document update'),
    )
    help = 'This is the Djapian daemon used to update the index based on djapian_change table.'

    requires_model_validation = True

    def handle(self, *app_labels, **options):
        verbose = options['verbose']

        make_daemon = options['make_daemon']
        loop = options['loop']
        timeout = options['timeout']
        rebuild_index = options['rebuild_index']
        per_page = options['per_page']
        commit_each = options['commit_each']

        utils.load_indexes()

        if make_daemon:
            become_daemon()

        if app_labels:
            try:
                app_list = [models.get_app(app_label) for app_label in app_labels]
            except (ImproperlyConfigured, ImportError), e:
                raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)
            for app in app_list:
                app_models = models.get_models(app, include_auto_created=True)
                if rebuild_index:
                    rebuild(verbose, per_page, commit_each, app_models)
                else:
                    update_changes(verbose, timeout,
                                   not (loop or make_daemon),
                                   per_page, commit_each, app_models)
        else:
            if rebuild_index:
                rebuild(verbose, per_page, commit_each)
            else:
                update_changes(verbose, timeout,
                               not (loop or make_daemon),
                               per_page, commit_each)

        if verbose:
            print '\n'
