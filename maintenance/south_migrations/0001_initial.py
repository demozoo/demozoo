# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Exclusion'
        db.create_table('maintenance_exclusion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('record_id', self.gf('django.db.models.fields.IntegerField')()),
            ('report_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('maintenance', ['Exclusion'])


    def backwards(self, orm):
        
        # Deleting model 'Exclusion'
        db.delete_table('maintenance_exclusion')


    models = {
        'maintenance.exclusion': {
            'Meta': {'object_name': 'Exclusion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'record_id': ('django.db.models.fields.IntegerField', [], {}),
            'report_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['maintenance']
