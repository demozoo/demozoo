from __future__ import absolute_import, unicode_literals

import os
import dotenv

# from fabric.api import hosts, cd, run, get, local, with_settings
from fabric import Connection, task
from invoke import run as local

dotenv.read_dotenv()

db_username = os.getenv('POSTGRES_USER', 'demozoo')

PRODUCTION_HOSTS = ['demozoo@www1.demozoo.org']
STAGING_HOSTS = ['demozoo@www2.demozoo.org']
DB_HOSTS = [{
    'host': 'demozoo@db1',
    'forward_agent': True,
    'gateway': Connection('demozoo@www1.demozoo.org'),
}]


@task(hosts=PRODUCTION_HOSTS)
def deploy(c):
    """Deploy the current git master to the live site"""
    c.run('cd /home/demozoo/demozoo && git pull')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
    c.run('cd /home/demozoo/demozoo && npm i --no-save')
    c.run('cd /home/demozoo/demozoo && npm run build')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py compress')
    c.run('sudo supervisorctl restart demozoo')
    c.run('sudo supervisorctl restart zxdemo')
    c.run('sudo supervisorctl restart demozoo-celery')
    c.run('sudo supervisorctl restart demozoo-celerybeat')


@task(hosts=STAGING_HOSTS)
def deploy_staging(c):
    """Deploy the current git 'staging' branch to the staging site"""
    c.run('cd /home/demozoo/demozoo && git pull')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
    c.run('cd /home/demozoo/demozoo && npm i --no-save')
    c.run('cd /home/demozoo/demozoo && npm run build')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput')
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py compress')
    c.run('sudo supervisorctl restart demozoo')
    c.run('sudo supervisorctl restart zxdemo')
    c.run('sudo supervisorctl restart demozoo-celery')
    c.run('sudo supervisorctl restart demozoo-celerybeat')


@task(hosts=PRODUCTION_HOSTS)
def sanity(c):
    """Fix up data integrity errors"""
    # pty=True stops Python from buffering output until the end of the run
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py sanity', pty=True)


@task(hosts=PRODUCTION_HOSTS)
def reindex(c):
    """Rebuild the search index from scratch. WARNING:SLOW"""
    # pty=True stops Python from buffering output until the end of the run
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py reindex', pty=True)


@task(hosts=STAGING_HOSTS)
def reindex_staging(c):
    """Rebuild the search index on staging from scratch. WARNING:SLOW"""
    # pty=True stops Python from buffering output until the end of the run
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py reindex', pty=True)


@task(hosts=PRODUCTION_HOSTS)
def bump_external_links(c):
    """Rescan external links for new 'recognised' sites"""
    # pty=True stops Python from buffering output until the end of the run
    c.run('cd /home/demozoo/demozoo && /home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py bump_external_links', pty=True)


@task(hosts=DB_HOSTS)
def fetchdb(c):
    """Pull the live database to the local copy"""
    c.run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
    c.get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
    c.run('rm /tmp/demozoo-fetchdb.sql.gz')
    local('dropdb -U%s demozoo' % db_username)
    local('createdb -U%s demozoo' % db_username)
    local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -U%s demozoo' % db_username)
    local('rm /tmp/demozoo-fetchdb.sql.gz')
