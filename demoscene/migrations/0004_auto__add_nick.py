# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Nick'
        db.create_table('demoscene_nick', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('releaser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='nicks', to=orm['demoscene.Releaser'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('demoscene', ['Nick'])


    def backwards(self, orm):
        
        # Deleting model 'Nick'
        db.delete_table('demoscene_nick')


    models = {
        'demoscene.downloadlink': {
            'Meta': {'object_name': 'DownloadLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'download_links'", 'to': "orm['demoscene.Production']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        },
        'demoscene.nick': {
            'Meta': {'object_name': 'Nick'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nicks'", 'to': "orm['demoscene.Releaser']"})
        },
        'demoscene.platform': {
            'Meta': {'object_name': 'Platform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'demoscene.production': {
            'Meta': {'object_name': 'Production'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': "orm['demoscene.Platform']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': "orm['demoscene.ProductionType']"})
        },
        'demoscene.productiontype': {
            'Meta': {'object_name': 'ProductionType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'demoscene.releaser': {
            'Meta': {'object_name': 'Releaser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_group': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['demoscene']
