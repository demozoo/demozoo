# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding M2M table for field competitions on 'Directory'
        db.create_table('sceneorg_directory_competitions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('directory', models.ForeignKey(orm['sceneorg.directory'], null=False)),
            ('competition', models.ForeignKey(orm['demoscene.competition'], null=False))
        ))
        db.create_unique('sceneorg_directory_competitions', ['directory_id', 'competition_id'])

        # Changing field 'FileDownload.data'
        db.alter_column('sceneorg_filedownload', 'data', self.gf('blob_field.BlobField')(null=True, blank=True))


    def backwards(self, orm):
        
        # Removing M2M table for field competitions on 'Directory'
        db.delete_table('sceneorg_directory_competitions')

        # Changing field 'FileDownload.data'
        db.alter_column('sceneorg_filedownload', 'data', self.gf('sceneorg.models.BlobField')(null=True, blank=True))


    models = {
        'demoscene.competition': {
            'Meta': {'object_name': 'Competition'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitions'", 'to': "orm['demoscene.Party']"}),
            'platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demoscene.Platform']", 'null': 'True', 'blank': 'True'}),
            'production_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demoscene.ProductionType']", 'null': 'True', 'blank': 'True'}),
            'shown_date_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'shown_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        },
        'demoscene.party': {
            'Meta': {'object_name': 'Party'},
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'end_date_date': ('django.db.models.fields.DateField', [], {}),
            'end_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'party_series': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parties'", 'to': "orm['demoscene.PartySeries']"}),
            'start_date_date': ('django.db.models.fields.DateField', [], {}),
            'start_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'woe_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'demoscene.partyseries': {
            'Meta': {'object_name': 'PartySeries'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pouet_party_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'twitter_username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'demoscene.platform': {
            'Meta': {'object_name': 'Platform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'photo_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'demoscene.productiontype': {
            'Meta': {'object_name': 'ProductionType'},
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'sceneorg.directory': {
            'Meta': {'object_name': 'Directory'},
            'competitions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sceneorg_directories'", 'symmetrical': 'False', 'to': "orm['demoscene.Competition']"}),
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
            'data': ('blob_field.BlobField', [], {'null': 'True', 'blank': 'True'}),
            'downloaded_at': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'downloads'", 'to': "orm['sceneorg.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sha1': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        }
    }

    complete_apps = ['sceneorg']
