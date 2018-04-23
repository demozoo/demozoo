# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from demoscene.utils.groklinks import grok_production_link

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        for download in orm.Download.objects.all():
            link = grok_production_link(download.url)
            download.link_class = link.__class__.__name__
            download.parameter = link.param
            download.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'mirror.archivemember': {
            'Meta': {'ordering': "['filename']", 'object_name': 'ArchiveMember'},
            'download': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'archive_members'", 'to': u"orm['mirror.Download']"}),
            'file_size': ('django.db.models.fields.IntegerField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'mirror.download': {
            'Meta': {'object_name': 'Download'},
            'downloaded_at': ('django.db.models.fields.DateTimeField', [], {}),
            'error_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'file_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'mirror_s3_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['mirror']
    symmetrical = True
