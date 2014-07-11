#!/usr/bin/env ruby

require 'rubygems'

system "pg_dump -c demozoo | gzip - > /home/demozoo/demozoo/data/demozoo.sql.gz"
system "s3cmd put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/hourly/demozoo-hourly-`date +%H`.sql.gz"
if Time.now.hour == 2
        system "s3cmd put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/daily/demozoo-daily-`date +%Y-%m-%d`.sql.gz"
end
