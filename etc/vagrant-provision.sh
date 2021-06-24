#!/bin/bash

PROJECT_DIR=/home/vagrant/demozoo
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/demozoo

PIP=$VIRTUALENV_DIR/bin/pip
PYTHON=$VIRTUALENV_DIR/bin/python

# Update APT database
apt-get update -y

# Python 3.8
apt-get install -y python3.8 python3.8-dev python3-pip python2

# PostgreSQL
apt-get install -y postgresql libpq-dev

# libffi
# (needed by bcrypt, which some old accounts still use as their password encryption method)
apt-get install -y libffi-dev

# node.js
curl -sL https://deb.nodesource.com/setup_12.x | bash -
apt-get install -y nodejs
npm install -g npm@latest

# virtualenvwrapper
pip3 install virtualenvwrapper
cat > /home/vagrant/.bashrc <<- EOM
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.8
export WORKON_HOME=\$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
workon demozoo
EOM

# Create virtualenv
su - vagrant -c "/usr/local/bin/virtualenv $VIRTUALENV_DIR --python=/usr/bin/python3.8"
su - vagrant -c "echo $PROJECT_DIR > $VIRTUALENV_DIR/.project"
su - vagrant -c "$PIP install -r $PROJECT_DIR/requirements.txt"

if [ ! -f $PROJECT_DIR/.env ]; then
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    cat > $PROJECT_DIR/.env <<-EOM
SECRET_KEY="$SECRET_KEY"

AWS_STORAGE_BUCKET_NAME="my-demozoo-media"

AWS_ACCESS_KEY_ID="get one from http://aws.amazon.com/s3/"
AWS_SECRET_ACCESS_KEY="get one from http://aws.amazon.com/s3/"

SCENEID_KEY="please read https://id.scene.org/docs/"
SCENEID_SECRET="please read https://id.scene.org/docs/"

POSTGRES_USER=vagrant

# Read-only mode:
# SITE_IS_WRITEABLE=0

# Disable debug toolbar in development:
# DEBUG_TOOLBAR_ENABLED=0
EOM
fi

# Create vagrant pgsql superuser
su - postgres -c "createuser -s vagrant"

# create database
su - vagrant -c "createdb demozoo"

# fetch database export
su - vagrant -c "wget http://data.demozoo.org/demozoo-export.sql.gz -O /home/vagrant/demozoo-export.sql.gz"
su - vagrant -c "gunzip -c /home/vagrant/demozoo-export.sql.gz | psql demozoo"

# migrate (in case the db schema in git is ahead of the live export)
su - vagrant -c "$PYTHON $PROJECT_DIR/manage.py migrate --settings=demozoo.settings.dev"

# Install project dependencies for node and run a first time
su - vagrant -c "cd ~/demozoo/ && npm i --no-save && npm run build"

