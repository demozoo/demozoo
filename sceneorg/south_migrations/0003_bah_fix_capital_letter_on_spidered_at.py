# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # rename field 'Directory.last_spidered_At'
        db.rename_column('sceneorg_directory', 'last_spidered_At', 'last_spidered_at')

    def backwards(self, orm):
        
        # rename field 'Directory.last_spidered_at'
        db.rename_column('sceneorg_directory', 'last_spidered_at', 'last_spidered_At')

    models = {
        'sceneorg.directory': {
            'Meta': {'object_name': 'Directory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {}),
            'last_spidered_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subdirectories'", 'null': 'True', 'to': "orm['sceneorg.Directory']"}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'sceneorg.file': {
            'Meta': {'object_name': 'File'},
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['sceneorg.Directory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['sceneorg']
