#!/bin/bash
SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
mkdir -p $PROJECT_DIR/demozoo/settings
cat > $PROJECT_DIR/demozoo/settings/local.py <<-EOM
SECRET_KEY = 'abc123'

from .dev import DATABASES
DATABASES['default']['USER'] = 'demozoo'
DATABASES['default']['PASSWORD'] = 'abc123'
DATABASES['default']['HOST'] = 'demozoo-db'

AWS_STORAGE_BUCKET_NAME = 'media.demozoo.org'
AWS_ACCESS_KEY_ID = 'get one from http://aws.amazon.com/s3/'
AWS_SECRET_ACCESS_KEY = 'get one from http://aws.amazon.com/s3/'

# Read-only mode:
# SITE_IS_WRITEABLE = False
EOM
