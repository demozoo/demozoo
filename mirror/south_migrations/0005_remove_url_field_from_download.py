# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Download.url'
        db.delete_column(u'mirror_download', 'url')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Download.url'
        raise RuntimeError("Cannot reverse this migration. 'Download.url' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Download.url'
        db.add_column(u'mirror_download', 'url',
                      self.gf('django.db.models.fields.CharField')(max_length=255),
                      keep_default=False)


    models = {
        u'mirror.archivemember': {
            'Meta': {'ordering': "['filename']", 'object_name': 'ArchiveMember'},
            'download': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_members'", 'to': u"orm['mirror.Download']"}),
            'file_size': ('django.db.models.fields.IntegerField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'mirror.download': {
            'Meta': {'ordering': "['link_class']", 'object_name': 'Download'},
            'downloaded_at': ('django.db.models.fields.DateTimeField', [], {}),
            'error_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'file_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'mirror_s3_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        }
    }

    complete_apps = ['mirror']