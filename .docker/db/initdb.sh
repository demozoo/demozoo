#!/bin/bash

# Create vagrant pgsql superuser
createuser -s vagrant

# create database
createdb demozoo

# fetch database export
wget http://data.demozoo.org/demozoo-export.sql.gz -O /home/vagrant/demozoo-export.sql.gz
gunzip -c /home/vagrant/demozoo-export.sql.gz | psql demozoo
