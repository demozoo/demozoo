# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Platform'
        db.create_table('demoscene_platform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('demoscene', ['Platform'])

        # Adding model 'ProductionType'
        db.create_table('demoscene_productiontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('demoscene', ['ProductionType'])

        # Adding model 'Production'
        db.create_table('demoscene_production', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('demoscene', ['Production'])

        # Adding M2M table for field platforms on 'Production'
        db.create_table('demoscene_production_platforms', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('production', models.ForeignKey(orm['demoscene.production'], null=False)),
            ('platform', models.ForeignKey(orm['demoscene.platform'], null=False))
        ))
        db.create_unique('demoscene_production_platforms', ['production_id', 'platform_id'])

        # Adding M2M table for field types on 'Production'
        db.create_table('demoscene_production_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('production', models.ForeignKey(orm['demoscene.production'], null=False)),
            ('productiontype', models.ForeignKey(orm['demoscene.productiontype'], null=False))
        ))
        db.create_unique('demoscene_production_types', ['production_id', 'productiontype_id'])


    def backwards(self, orm):
        
        # Deleting model 'Platform'
        db.delete_table('demoscene_platform')

        # Deleting model 'ProductionType'
        db.delete_table('demoscene_productiontype')

        # Deleting model 'Production'
        db.delete_table('demoscene_production')

        # Removing M2M table for field platforms on 'Production'
        db.delete_table('demoscene_production_platforms')

        # Removing M2M table for field types on 'Production'
        db.delete_table('demoscene_production_types')


    models = {
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
        }
    }

    complete_apps = ['demoscene']
