from __future__ import with_statement
from fabric.api import *

env.hosts = ['demozoo@web.dkev.org:5711']


def deploy():
	with cd('/home/demozoo/demozoo'):
		run('git pull')
		run('/home/demozoo/.virtualenvs/demozoo/bin/pip install -r requirements-production.txt')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py syncdb --settings=settings.production')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py syncdb --database=geonameslite --settings=settings.production')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py migrate --settings=settings.production')
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py collectstatic --noinput --settings=settings.production')
		run('sudo supervisorctl restart demozoo')
		run('sudo supervisorctl restart demozoo-celery')
		run('sudo supervisorctl restart demozoo-celerybeat')


def sanity():
	with cd('/home/demozoo/demozoo'):
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py sanity --settings=settings.production')


def reindex():
	with cd('/home/demozoo/demozoo'):
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py force_rebuild_index --settings=settings.production')


def bump_external_links():
	with cd('/home/demozoo/demozoo'):
		run('/home/demozoo/.virtualenvs/demozoo/bin/python ./manage.py bump_external_links --settings=settings.production')


def fetchdb():
	run('pg_dump -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
	get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
	run('rm /tmp/demozoo-fetchdb.sql.gz')
	local('dropdb -Upostgres demozoo')
	local('createdb -Upostgres demozoo')
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -Upostgres demozoo')
	local('rm /tmp/demozoo-fetchdb.sql.gz')
