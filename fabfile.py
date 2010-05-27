from __future__ import with_statement
from fabric.api import *

env.hosts = ['root@altaria.vm.bytemark.co.uk']

def deploy():
	with cd('/var/www/demozoo2'):
		run('svn up')
		run('./manage.py syncdb')
		run('./manage.py migrate')
		run('/etc/init.d/apache2 reload')
