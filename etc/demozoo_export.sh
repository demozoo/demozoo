#!/bin/sh

pg_dump -h db1 -w -c demozoo -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql -h db1 -w demozoo_export -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql -h db1 -w demozoo_export -c "UPDATE auth_user SET email='', password='"'!'"', first_name='', last_name='';"
psql -h db1 -w demozoo_export -c "UPDATE demoscene_releaser SET first_name='' WHERE show_first_name='f';"
psql -h db1 -w demozoo_export -c "UPDATE demoscene_releaser SET surname='' WHERE show_surname='f';"
psql -h db1 -w demozoo_export -c "UPDATE productions_production SET search_document=NULL;"
psql -h db1 -w demozoo_export -c "UPDATE demoscene_releaser SET search_document=NULL, admin_search_document=NULL;"
psql -h db1 -w demozoo_export -c "UPDATE parties_party SET search_document=NULL;"
psql -h db1 -w demozoo_export -c "TRUNCATE TABLE celery_taskmeta, celery_tasksetmeta, django_session, djcelery_intervalschedule, djcelery_periodictask, djcelery_crontabschedule, djcelery_periodictasks, djcelery_taskstate, djcelery_workerstate;"
psql -h db1 -w demozoo_export -c "TRUNCATE TABLE janeway_author, janeway_credit, janeway_downloadlink, janeway_membership, janeway_name, janeway_packcontent, janeway_release, janeway_release_author_names, janeway_releasetype, janeway_soundtracklink;"
psql -h db1 -w demozoo_export -c "TRUNCATE TABLE awards_recommendation;"

pg_dump -h db1 -w -O demozoo_export | gzip - > /home/demozoo/demozoo/data/demozoo-export.sql.gz

s3cmd put -P /home/demozoo/demozoo/data/demozoo-export.sql.gz s3://data.demozoo.org/demozoo-export.sql.gz
