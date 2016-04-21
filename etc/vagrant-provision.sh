#!/bin/bash

PROJECT_DIR=/home/vagrant/demozoo
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/demozoo

PIP=$VIRTUALENV_DIR/bin/pip

# Update APT database
apt-get update -y

# Python 2.7
apt-get install -y python python-dev python-pip

# PostgreSQL
apt-get install -y postgresql libpq-dev

# libffi
# (needed by bcrypt, which some old accounts still use as their password encryption method)
apt-get install -y libffi-dev

# xapian (search engine)
apt-get install -y python-xapian

# node.js / lessc
curl -sL https://deb.nodesource.com/setup_4.x | bash -
apt-get install -y nodejs
npm install -g less

# virtualenvwrapper
pip install virtualenvwrapper
cat > /home/vagrant/.bashrc <<- EOM
export WORKON_HOME=\$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon demozoo
EOM

# Create virtualenv
su - vagrant -c "/usr/local/bin/virtualenv $VIRTUALENV_DIR"
su - vagrant -c "echo $PROJECT_DIR > $VIRTUALENV_DIR/.project"
su - vagrant -c "$PIP install -r $PROJECT_DIR/requirements.txt"

if [ ! -f $PROJECT_DIR/settings/local.py ]; then
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    cat > $PROJECT_DIR/settings/local.py <<-EOM
SECRET_KEY = '$SECRET_KEY'

from .dev import DATABASES
DATABASES['default']['USER'] = 'vagrant'

AWS_STORAGE_BUCKET_NAME = 'media.demozoo.org'
AWS_ACCESS_KEY_ID = 'get one from http://aws.amazon.com/s3/'
AWS_SECRET_ACCESS_KEY = 'get one from http://aws.amazon.com/s3/'

# Read-only mode:
# SITE_IS_WRITEABLE = False
EOM
fi

# link xapian into virtualenv
su - vagrant -c "ln -s /usr/lib/python2.7/dist-packages/xapian $VIRTUALENV_DIR/lib/python2.7/site-packages/"

# Create vagrant pgsql superuser
su - postgres -c "createuser -s vagrant"

# create database
su - vagrant -c "createdb demozoo"
# fetch database export
su - vagrant -c "wget http://data.demozoo.org/demozoo-export.sql.gz -O /home/vagrant/demozoo-export.sql.gz"
su - vagrant -c "gunzip -c /home/vagrant/demozoo-export.sql.gz | psql demozoo"
