# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Directory'
        db.create_table('sceneorg_directory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('last_seen_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('last_spidered_At', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('sceneorg', ['Directory'])

        # Adding model 'File'
        db.create_table('sceneorg_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('last_seen_at', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('sceneorg', ['File'])


    def backwards(self, orm):
        
        # Deleting model 'Directory'
        db.delete_table('sceneorg_directory')

        # Deleting model 'File'
        db.delete_table('sceneorg_file')


    models = {
        'sceneorg.directory': {
            'Meta': {'object_name': 'Directory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {}),
            'last_spidered_At': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'sceneorg.file': {
            'Meta': {'object_name': 'File'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['sceneorg']
