# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FileDownload'
        db.create_table('sceneorg_filedownload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='downloads', to=orm['sceneorg.File'])),
            ('downloaded_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('data', self.gf('sceneorg.models.BlobField')(null=True, blank=True)),
            ('sha1', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('sceneorg', ['FileDownload'])


    def backwards(self, orm):
        
        # Deleting model 'FileDownload'
        db.delete_table('sceneorg_filedownload')


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
        },
        'sceneorg.filedownload': {
            'Meta': {'object_name': 'FileDownload'},
            'data': ('sceneorg.models.BlobField', [], {'null': 'True', 'blank': 'True'}),
            'downloaded_at': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'downloads'", 'to': "orm['sceneorg.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        }
    }

    complete_apps = ['sceneorg']
