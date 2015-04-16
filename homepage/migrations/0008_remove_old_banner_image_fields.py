# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Banner.image'
        db.delete_column(u'homepage_banner', 'image')

        # Deleting field 'Banner.image_height'
        db.delete_column(u'homepage_banner', 'image_height')

        # Deleting field 'Banner.image_width'
        db.delete_column(u'homepage_banner', 'image_width')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Banner.image'
        raise RuntimeError("Cannot reverse this migration. 'Banner.image' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Banner.image'
        db.add_column(u'homepage_banner', 'image',
                      self.gf('django.db.models.fields.files.ImageField')(max_length=100),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Banner.image_height'
        raise RuntimeError("Cannot reverse this migration. 'Banner.image_height' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Banner.image_height'
        db.add_column(u'homepage_banner', 'image_height',
                      self.gf('django.db.models.fields.IntegerField')(),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Banner.image_width'
        raise RuntimeError("Cannot reverse this migration. 'Banner.image_width' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Banner.image_width'
        db.add_column(u'homepage_banner', 'image_width',
                      self.gf('django.db.models.fields.IntegerField')(),
                      keep_default=False)


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