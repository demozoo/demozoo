# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from django.conf import settings


class Migration(SchemaMigration):

    def forwards(self, orm):
        try:
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        except AttributeError:
            bucket_name = 'media.demozoo.org'

        try:
            bucket_format = settings.AWS_BOTO_CALLING_FORMAT
        except AttributeError:
            bucket_format = 'VHostCallingFormat'

        if bucket_format == 'VHostCallingFormat':
            url_prefix = "http://%s/" % bucket_name
        else:
            url_prefix = "http://%s.s3.amazonaws.com/" % bucket_name

        # Adding field 'Platform.photo_url'
        db.add_column(u'platforms_platform', 'photo_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'Platform.thumbnail_url'
        db.add_column(u'platforms_platform', 'thumbnail_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        db.execute("UPDATE platforms_platform SET photo_url = %s || photo WHERE photo IS NOT NULL", [url_prefix])
        db.execute("UPDATE platforms_platform SET thumbnail_url = %s || thumbnail WHERE thumbnail IS NOT NULL", [url_prefix])

    def backwards(self, orm):
        # Deleting field 'Platform.photo_url'
        db.delete_column(u'platforms_platform', 'photo_url')

        # Deleting field 'Platform.thumbnail_url'
        db.delete_column(u'platforms_platform', 'thumbnail_url')


    models = {
        u'platforms.platform': {
            'Meta': {'ordering': "['name']", 'object_name': 'Platform'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'photo_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'photo_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['platforms']