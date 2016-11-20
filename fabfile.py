from __future__ import with_statement
from fabric.api import env, cd, run, get, local

from settings.dev import DATABASES
db_username = DATABASES['default']['USER']

env.hosts = ['demozoo@www1.demozoo.org']


def deploy():
	"""Deploy the current git master to the live site"""
	with cd('/home/demozoo/demozoo'):
		run('git pull')
		run('/home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
		run('npm install')
		run('grunt')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py syncdb --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py compress --settings=settings.productionvm')
		run('sudo supervisorctl restart demozoo')
		run('sudo supervisorctl restart zxdemo')
		run('sudo supervisorctl restart demozoo-celery')
		run('sudo supervisorctl restart demozoo-celerybeat')


def sanity():
	"""Fix up data integrity errors"""
	with cd('/home/demozoo/demozoo'):
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py sanity --settings=settings.productionvm')


def reindex():
	"""Rebuild the search index from scratch. WARNING:SLOW"""
	with cd('/home/demozoo/demozoo'):
		run('sudo supervisorctl stop demozoo-djapian')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py force_rebuild_index --settings=settings.productionvm')
		run('sudo supervisorctl start demozoo-djapian')


def bump_external_links():
	"""Rescan external links for new 'recognised' sites"""
	with cd('/home/demozoo/demozoo'):
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py bump_external_links --settings=settings.productionvm')


def fetchdb():
	"""Pull the live database to the local copy"""
	run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
	get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
	run('rm /tmp/demozoo-fetchdb.sql.gz')
	local('dropdb -U%s demozoo' % db_username)
	local('createdb -U%s demozoo' % db_username)
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -U%s demozoo' % db_username)
	local('rm /tmp/demozoo-fetchdb.sql.gz')


def exportdb():
	"""Dump the live DB with personal info redacted"""
	run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
	get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
	run('rm /tmp/demozoo-fetchdb.sql.gz')
	local('createdb -U%s demozoo_dump' % db_username)
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -U%s demozoo_dump' % db_username)
	local('rm /tmp/demozoo-fetchdb.sql.gz')
	local("""psql -U%s demozoo_dump -c "UPDATE auth_user SET email='', password='!', first_name='', last_name='';" """ % db_username)
	local("""psql -U%s demozoo_dump -c "UPDATE demoscene_releaser SET first_name='' WHERE show_first_name='f';" """ % db_username)
	local("""psql -U%s demozoo_dump -c "UPDATE demoscene_releaser SET surname='' WHERE show_surname='f';" """ % db_username)
	local("""psql -U%s demozoo_dump -c "DROP TABLE celery_taskmeta; DROP TABLE celery_tasksetmeta; DROP TABLE django_session; DROP TABLE djapian_change;" """ % db_username)
	local('pg_dump -Z1 -cf demozoo-export.sql.gz demozoo_dump')
	#local('dropdb -U%s demozoo_dump' % db_username)
