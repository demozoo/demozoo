# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Banner'
        db.create_table('homepage_banner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('image_width', self.gf('django.db.models.fields.IntegerField')()),
            ('image_height', self.gf('django.db.models.fields.IntegerField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('show_for_anonymous_users', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('show_for_logged_in_users', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('homepage', ['Banner'])

        # Adding model 'Teaser'
        db.create_table('homepage_teaser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('image_width', self.gf('django.db.models.fields.IntegerField')()),
            ('image_height', self.gf('django.db.models.fields.IntegerField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('show_for_anonymous_users', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('show_for_logged_in_users', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('homepage', ['Teaser'])


    def backwards(self, orm):
        
        # Deleting model 'Banner'
        db.delete_table('homepage_banner')

        # Deleting model 'Teaser'
        db.delete_table('homepage_teaser')


    models = {
        'homepage.banner': {
            'Meta': {'object_name': 'Banner'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'image_height': ('django.db.models.fields.IntegerField', [], {}),
            'image_width': ('django.db.models.fields.IntegerField', [], {}),
            'show_for_anonymous_users': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'show_for_logged_in_users': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'homepage.teaser': {
            'Meta': {'object_name': 'Teaser'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'image_height': ('django.db.models.fields.IntegerField', [], {}),
            'image_width': ('django.db.models.fields.IntegerField', [], {}),
            'show_for_anonymous_users': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'show_for_logged_in_users': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['homepage']
