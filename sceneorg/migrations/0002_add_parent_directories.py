# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Directory.parent'
        db.add_column('sceneorg_directory', 'parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subdirectories', null=True, to=orm['sceneorg.Directory']), keep_default=False)

        # Adding field 'File.directory'
        db.add_column('sceneorg_file', 'directory', self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='files', to=orm['sceneorg.Directory']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Directory.parent'
        db.delete_column('sceneorg_directory', 'parent_id')

        # Deleting field 'File.directory'
        db.delete_column('sceneorg_file', 'directory_id')


    models = {
        'sceneorg.directory': {
            'Meta': {'object_name': 'Directory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_seen_at': ('django.db.models.fields.DateTimeField', [], {}),
            'last_spidered_At': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
