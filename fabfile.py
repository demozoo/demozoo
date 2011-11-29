from __future__ import with_statement
from fabric.api import *

env.hosts = ['demozoo@altaria.vm.bytemark.co.uk']

def deploy():
	with cd('/var/www/demozoo2'):
		run('svn up')
		run('source /home/demozoo/virtualenv/bin/activate && pip install -E /home/demozoo/virtualenv/ -r /var/www/demozoo2/requirements.txt')
		run('./manage.py syncdb')
		run('./manage.py migrate')
		run('sudo /etc/init.d/apache2 reload')

def sanity():
	with cd('/var/www/demozoo2'):
		run('./manage.py sanity')

def reindex():
	with cd('/var/www/demozoo2'):
		run('./manage.py force_rebuild_index')
