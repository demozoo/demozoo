#!/bin/sh

pg_dump -c demozoo -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql demozoo_export -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql demozoo_export -c "UPDATE auth_user SET email='', password='"'!'"', first_name='', last_name='';"
psql demozoo_export -c "UPDATE demoscene_releaser SET first_name='' WHERE show_first_name='f';"
psql demozoo_export -c "UPDATE demoscene_releaser SET surname='' WHERE show_surname='f';"
psql demozoo_export -c "UPDATE productions_production SET search_document=NULL;"
psql demozoo_export -c "UPDATE demoscene_releaser SET search_document=NULL, admin_search_document=NULL;"
psql demozoo_export -c "UPDATE parties_party SET search_document=NULL;"
psql demozoo_export -c "TRUNCATE TABLE celery_taskmeta, celery_tasksetmeta, django_session, djcelery_intervalschedule, djcelery_periodictask, djcelery_crontabschedule, djcelery_periodictasks, djcelery_taskstate, djcelery_workerstate;"
psql demozoo_export -c "TRUNCATE TABLE janeway_name, janeway_membership, janeway_author, janeway_release, janeway_releasetype, janeway_credit, janeway_release_author_names;"

pg_dump -O demozoo_export | gzip - > /home/demozoo/demozoo/data/demozoo-export.sql.gz

s3cmd put -P /home/demozoo/demozoo/data/demozoo-export.sql.gz s3://data.demozoo.org/demozoo-export.sql.gz
