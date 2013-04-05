from __future__ import with_statement
from fabric.api import *

env.hosts = ['demozoo@altaria.vm.bytemark.co.uk']


def deploy():
	with cd('/var/www/demozoo2'):
		run('git pull')
		run('source /home/demozoo/virtualenv/bin/activate && pip install -E /home/demozoo/virtualenv/ -r /var/www/demozoo2/requirements.txt')
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py syncdb')
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py migrate')
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py collectstatic --noinput')
		run('sudo /etc/init.d/apache2 reload')


def sanity():
	with cd('/var/www/demozoo2'):
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py sanity')


def reindex():
	with cd('/var/www/demozoo2'):
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py force_rebuild_index')


def bump_external_links():
	with cd('/var/www/demozoo2'):
		run('source /home/demozoo/virtualenv/bin/activate && ./manage.py bump_external_links')


def fetchdb():
	run('pg_dump -Upostgres -Z1 -cf /tmp/demozoo-fetchdb.sql.gz demozoo')
	get('/tmp/demozoo-fetchdb.sql.gz', '/tmp/demozoo-fetchdb.sql.gz')
	run('rm /tmp/demozoo-fetchdb.sql.gz')
	local('dropdb -Upostgres demozoo')
	local('createdb -Upostgres demozoo')
	local('gzcat /tmp/demozoo-fetchdb.sql.gz | psql -Upostgres demozoo')
	local('rm /tmp/demozoo-fetchdb.sql.gz')
