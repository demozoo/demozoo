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

        # Adding field 'NewsStory.image_url'
        db.add_column(u'homepage_newsimage', 'image_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        # Adding field 'BannerImage.image_url'
        db.add_column(u'homepage_bannerimage', 'image_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)

        db.execute("UPDATE homepage_newsimage SET image_url = %s || image WHERE image IS NOT NULL", [url_prefix])
        db.execute("UPDATE homepage_bannerimage SET image_url = %s || image WHERE image IS NOT NULL", [url_prefix])


    def backwards(self, orm):
        # Deleting field 'NewsStory.image_url'
        db.delete_column(u'homepage_newsimage', 'image_url')

        # Deleting field 'BannerImage.image_url'
        db.delete_column(u'homepage_bannerimage', 'image_url')


    models = {
        u'homepage.banner': {
            'Meta': {'object_name': 'Banner'},
            'banner_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['homepage.BannerImage']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'show_for_anonymous_users': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_for_logged_in_users': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'homepage.bannerimage': {
            'Meta': {'object_name': 'BannerImage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'image_height': ('django.db.models.fields.IntegerField', [], {}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'image_width': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'homepage.newsimage': {
            'Meta': {'object_name': 'NewsImage'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'image_height': ('django.db.models.fields.IntegerField', [], {}),
            'image_width': ('django.db.models.fields.IntegerField', [], {}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'homepage.newsstory': {
            'Meta': {'object_name': 'NewsStory'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['homepage.NewsImage']"}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['homepage']