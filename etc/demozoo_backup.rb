#!/usr/bin/env ruby

require 'rubygems'
require 'mail'

system "pg_dump -c demozoo | gzip - > /home/demozoo/demozoo/data/demozoo.sql.gz"
system "s3cmd put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/hourly/demozoo-hourly-`date +%H`.sql.gz"
if Time.now.hour == 2
        system "s3cmd put /home/demozoo/demozoo/data/demozoo.sql.gz s3://demozoo-backups/daily/demozoo-daily-`date +%Y-%m-%d`.sql.gz"
        if Time.now.wday == 6
                Mail.deliver do
                        from 'Demozoo backups <matt@west.co.tt>'
                        to ['matt@west.co.tt','jensadne@pvv.ntnu.no']
                        subject 'Demozoo database backup'
                        body "Hello! Here's the Demozoo backup for this week.\n\nLove,\nthe server\n"
                        add_file '/home/demozoo/demozoo/data/demozoo.sql.gz'
                end
        end
end
