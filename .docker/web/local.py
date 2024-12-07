import os

from .dev import DATABASES


SECRET_KEY = os.environ.get('SECRET_KEY')

DATABASES['default']['USER'] = os.environ.get('POSTGRES_USER')
DATABASES['default']['PASSWORD'] = os.environ.get('POSTGRES_PASSWORD')
DATABASES['default']['HOST'] = os.environ.get('POSTGRES_HOST')

AWS_STORAGE_BUCKET_NAME = 'media.demozoo.org'
AWS_ACCESS_KEY_ID = 'get one from http://aws.amazon.com/s3/'
AWS_SECRET_ACCESS_KEY = 'get one from http://aws.amazon.com/s3/'
