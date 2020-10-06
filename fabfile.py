from __future__ import absolute_import, unicode_literals

import os
import dotenv

from fabric.api import hosts, cd, run, get, local, with_settings

dotenv.read_dotenv()

db_username = os.getenv('POSTGRES_USER', 'demozoo')

PRODUCTION_HOSTS = ['demozoo@www1.demozoo.org']
STAGING_HOSTS = ['demozoo@www2.demozoo.org']
DB_HOSTS = ['demozoo@db1']
DB_GATEWAY = 'demozoo@www1.demozoo.org'


@hosts(PRODUCTION_HOSTS)
def deploy():
    """Deploy the current git master to the live site"""
    with cd('/home/demozoo/demozoo'):
        run('git pull')
        run('/home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
        run('npm i --no-save')
        run('npm run build')
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate --settings=demozoo.settings.productionvm')
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput --settings=demozoo.settings.productionvm')
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py compress --settings=demozoo.settings.productionvm')
        run('sudo supervisorctl restart demozoo')
        run('sudo supervisorctl restart zxdemo')
        run('sudo supervisorctl restart demozoo-celery')
        run('sudo supervisorctl restart demozoo-celerybeat')


@hosts(STAGING_HOSTS)
def deploy_staging():
    """Deploy the current git 'staging' branch to the staging site"""
    with cd('/home/demozoo/demozoo-staging'):
        run('git pull')
        run('/home/demozoo/.virtualenvs/demozoo-staging/bin/pip install -r requirements-production.txt')
        run('npm i --no-save')
        run('npm run build')
        run('/home/demozoo/.virtualenvs/demozoo-staging/bin/python ./manage.py migrate --settings=demozoo.settings.staging')
        run('/home/demozoo/.virtualenvs/demozoo-staging/bin/python ./manage.py collectstatic --noinput --settings=demozoo.settings.staging')
        run('/home/demozoo/.virtualenvs/demozoo-staging/bin/python ./manage.py compress --settings=demozoo.settings.staging')
        run('sudo supervisorctl restart demozoo-staging')


@hosts(PRODUCTION_HOSTS)
def sanity():
    """Fix up data integrity errors"""
    with cd('/home/demozoo/demozoo'):
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py sanity --settings=demozoo.settings.productionvm')


@hosts(PRODUCTION_HOSTS)
def reindex():
    """Rebuild the search index from scratch. WARNING:SLOW"""
    with cd('/home/demozoo/demozoo'):
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py reindex --settings=demozoo.settings.productionvm')


@hosts(STAGING_HOSTS)
def reindex_staging():
    """Rebuild the search index on staging from scratch. WARNING:SLOW"""
    with cd('/home/demozoo/demozoo-staging'):
        run('/home/demozoo/.virtualenvs/demozoo-staging/bin/python ./manage.py reindex --settings=demozoo.settings.staging')


@hosts(PRODUCTION_HOSTS)
def bump_external_links():
    """Rescan external links for new 'recognised' sites"""
    with cd('/home/demozoo/demozoo'):
        run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py bump_external_links --settings=demozoo.settings.productionvm')


@with_settings(forward_agent=True, gateway=DB_GATEWAY)
@hosts(DB_HOSTS)
def fetchdb():
    """Pull the live database to the local copy"""
    run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
    get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
    run('rm /tmp/demozoo-fetchdb.sql.gz')
    local('dropdb -U%s demozoo' % db_username)
    local('createdb -U%s demozoo' % db_username)
    local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -U%s demozoo' % db_username)
    local('rm /tmp/demozoo-fetchdb.sql.gz')
