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


# virtualenvwrapper
pip install virtualenvwrapper
cat > /home/vagrant/.bashrc <<- EOM
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon demozoo
EOM

# Create virtualenv
su - vagrant -c "/usr/local/bin/virtualenv $VIRTUALENV_DIR"
su - vagrant -c "$PIP install -r $PROJECT_DIR/requirements.txt"

# link xapian into virtualenv
su - vagrant -c "ln -s /usr/lib/python2.7/dist-packages/xapian ~/.virtualenvs/demozoo/lib/python2.7/site-packages/"

# Create vagrant pgsql superuser
su - postgres -c "createuser -s vagrant"

# create database
su - vagrant -c "createdb demozoo"
# fetch database export
su - vagrant -c "wget http://data.demozoo.org/demozoo-export.sql.gz -o /home/vagrant/demozoo-export.sql.gz"
su - vagrant -c "gunzip -c /home/vagrant/demozoo-export.sql.gz | psql demozoo"
