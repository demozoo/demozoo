# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Download'
        db.create_table('mirror_download', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('downloaded_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('sha1', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('md5', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('error_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('file_size', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('mirror_s3_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('mirror', ['Download'])


    def backwards(self, orm):
        
        # Deleting model 'Download'
        db.delete_table('mirror_download')


    models = {
        'mirror.download': {
            'Meta': {'object_name': 'Download'},
            'downloaded_at': ('django.db.models.fields.DateTimeField', [], {}),
            'error_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'file_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'mirror_s3_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['mirror']
