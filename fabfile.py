from __future__ import with_statement
from fabric.api import env, cd, run, get, local

env.hosts = ['demozoo@matilda.demozoo.org']


def deploy():
	"""Deploy the current git master to the live site"""
	with cd('/home/demozoo/demozoo'):
		run('git pull')
		run('/home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py syncdb --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py syncdb --database=geonameslite --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate --settings=settings.productionvm')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput --settings=settings.productionvm')
		run('sudo supervisorctl restart demozoo')
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
	local('dropdb -Upostgres demozoo')
	local('createdb -Upostgres demozoo')
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -Upostgres demozoo')
	local('rm /tmp/demozoo-fetchdb.sql.gz')

def exportdb():
	"""Dump the live DB with personal info redacted"""
	run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
	get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
	run('rm /tmp/demozoo-fetchdb.sql.gz')
	local('createdb -Upostgres demozoo_dump')
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -Upostgres demozoo_dump')
	local('rm /tmp/demozoo-fetchdb.sql.gz')
	local("""psql -Upostgres demozoo_dump -c "UPDATE auth_user SET email='', password='!', first_name='', last_name='';" """)
	local("""psql -Upostgres demozoo_dump -c "UPDATE demoscene_releaser SET first_name='' WHERE show_first_name='f';" """)
	local("""psql -Upostgres demozoo_dump -c "UPDATE demoscene_releaser SET surname='' WHERE show_surname='f';" """)
	local("""psql -Upostgres demozoo_dump -c "DROP TABLE celery_taskmeta; DROP TABLE celery_tasksetmeta; DROP TABLE django_session; DROP TABLE djapian_change;" """)
	local('pg_dump -Z1 -cf demozoo-export.sql.gz demozoo_dump')
	#local('dropdb -Upostgres demozoo_dump')
