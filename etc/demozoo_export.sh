#!/bin/sh

# NOTE: This script is run from the database server. If it changes, it must be
# copied there manually.

. /home/demozoo/demozoo/.env
export PGPASSWORD=$POSTGRES_PASSWORD

pg_dump -h $POSTGRES_HOST -w -c demozoo -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql -h $POSTGRES_HOST -w demozoo_export -f /home/demozoo/demozoo/data/demozoo-export-raw.sql
psql -h $POSTGRES_HOST -w demozoo_export -c "UPDATE auth_user SET email='', password='"'!'"', first_name='', last_name='';"
psql -h $POSTGRES_HOST -w demozoo_export -c "UPDATE productions_production SET search_document=NULL;"
psql -h $POSTGRES_HOST -w demozoo_export -c "UPDATE demoscene_releaser SET search_document=NULL, real_name_note='';"
psql -h $POSTGRES_HOST -w demozoo_export -c "UPDATE parties_party SET search_document=NULL;"
psql -h $POSTGRES_HOST -w demozoo_export -c "UPDATE awards_event SET juror_feed_url='';"
psql -h $POSTGRES_HOST -w demozoo_export -c "TRUNCATE TABLE celery_taskmeta, celery_tasksetmeta, django_session, djcelery_intervalschedule, djcelery_periodictask, djcelery_crontabschedule, djcelery_periodictasks, djcelery_taskstate, djcelery_workerstate;"
psql -h $POSTGRES_HOST -w demozoo_export -c "TRUNCATE TABLE janeway_author, janeway_credit, janeway_downloadlink, janeway_membership, janeway_name, janeway_packcontent, janeway_release, janeway_release_author_names, janeway_releasetype, janeway_screenshot, janeway_soundtracklink;"
psql -h $POSTGRES_HOST -w demozoo_export -c "TRUNCATE TABLE awards_recommendation, awards_juror, awards_screeningcomment, awards_screeningdecision;"

pg_dump -h $POSTGRES_HOST -w -O demozoo_export | gzip - > /home/demozoo/demozoo/data/demozoo-export.sql.gz

s3cmd --access_key=$AWS_ACCESS_KEY_ID --secret_key=$AWS_SECRET_ACCESS_KEY put -P /home/demozoo/demozoo/data/demozoo-export.sql.gz s3://data.demozoo.org/demozoo-export.sql.gz
