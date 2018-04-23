# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ArchiveMember.archive_sha1'
        db.add_column(u'mirror_archivemember', 'archive_sha1',
                      self.gf('django.db.models.fields.CharField')(db_index=True, default='', max_length=40, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ArchiveMember.archive_sha1'
        db.delete_column(u'mirror_archivemember', 'archive_sha1')


    models = {
        u'mirror.archivemember': {
            'Meta': {'ordering': "['filename']", 'object_name': 'ArchiveMember'},
            'archive_sha1': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '40', 'blank': 'True'}),
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