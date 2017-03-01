# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ArchiveMember'
        db.create_table('mirror_archivemember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('download', self.gf('django.db.models.fields.related.ForeignKey')(related_name='archive_members', to=orm['mirror.Download'])),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file_size', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('mirror', ['ArchiveMember'])


    def backwards(self, orm):
        
        # Deleting model 'ArchiveMember'
        db.delete_table('mirror_archivemember')


    models = {
        'mirror.archivemember': {
            'Meta': {'object_name': 'ArchiveMember'},
            'download': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_members'", 'to': "orm['mirror.Download']"}),
            'file_size': ('django.db.models.fields.IntegerField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
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
