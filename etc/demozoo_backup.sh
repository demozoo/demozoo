#!/bin/sh

. /home/demozoo/demozoo/.env
export PGPASSWORD=$POSTGRES_PASSWORD

pg_dump -h $POSTGRES_HOST -w -c demozoo | gzip - > /home/demozoo/demozoo/data/demozoo.sql.gz
s3cmd --access_key=$AWS_ACCESS_KEY_ID --secret_key=$AWS_SECRET_ACCESS_KEY put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/hourly/demozoo-hourly-`date +%H`.sql.gz
if [ $(date +%H) -eq 2 ] ; then
    s3cmd --access_key=$AWS_ACCESS_KEY_ID --secret_key=$AWS_SECRET_ACCESS_KEY put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/daily/demozoo-daily-`date +%Y-%m-%d`.sql.gz
fi
sudo ln -f /home/demozoo/demozoo/data/demozoo.sql.gz /demozoo-backups/
