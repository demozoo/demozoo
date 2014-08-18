# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Production', fields ['sortable_title']
        db.create_index(u'productions_production', ['sortable_title'])
        db.execute("DROP INDEX demoscene_production_lower_title")


    def backwards(self, orm):
        # Removing index on 'Production', fields ['sortable_title']
        db.delete_index(u'productions_production', ['sortable_title'])
        db.execute("CREATE INDEX demoscene_production_lower_title ON productions_production (lower(productions_production.title))")


    models = {
        u'demoscene.nick': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('releaser', 'name'),)", 'object_name': 'Nick'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'differentiator': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nicks'", 'to': u"orm['demoscene.Releaser']"})
        },
        u'demoscene.releaser': {
            'Meta': {'ordering': "['name']", 'object_name': 'Releaser'},
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'geonames_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_group': ('django.db.models.fields.BooleanField', [], {}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'real_name_note': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'show_first_name': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'show_surname': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'woe_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'platforms.platform': {
            'Meta': {'ordering': "['name']", 'object_name': 'Platform'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'photo_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'productions.credit': {
            'Meta': {'ordering': "['production__title']", 'object_name': 'Credit'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credits'", 'to': u"orm['demoscene.Nick']"}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credits'", 'to': u"orm['productions.Production']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'productions.packmember': {
            'Meta': {'ordering': "['position']", 'object_name': 'PackMember'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'packed_in'", 'to': u"orm['productions.Production']"}),
            'pack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pack_members'", 'to': u"orm['productions.Production']"}),
            'position': ('django.db.models.fields.IntegerField', [], {})
        },
        u'productions.production': {
            'Meta': {'ordering': "['title']", 'object_name': 'Production'},
            'author_affiliation_nicks': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'member_productions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['demoscene.Nick']"}),
            'author_nicks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'productions'", 'blank': 'True', 'to': u"orm['demoscene.Nick']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'default_screenshot': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['productions.Screenshot']"}),
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'has_bonafide_edits': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include_notes_in_search': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'productions'", 'blank': 'True', 'to': u"orm['platforms.Platform']"}),
            'release_date_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'scene_org_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sortable_title': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'supertype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': u"orm['productions.ProductionType']"}),
            'unparsed_byline': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'productions.productionblurb': {
            'Meta': {'object_name': 'ProductionBlurb'},
            'body': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blurbs'", 'to': u"orm['productions.Production']"})
        },
        u'productions.productiondemozoo0platform': {
            'Meta': {'object_name': 'ProductionDemozoo0Platform'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'demozoo0_platforms'", 'to': u"orm['productions.Production']"})
        },
        u'productions.productionlink': {
            'Meta': {'ordering': "['link_class']", 'unique_together': "(('link_class', 'parameter', 'production', 'is_download_link'),)", 'object_name': 'ProductionLink'},
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'file_for_screenshot': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_download_link': ('django.db.models.fields.BooleanField', [], {}),
            'is_unresolved_for_screenshotting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': u"orm['productions.Production']"})
        },
        u'productions.productiontype': {
            'Meta': {'object_name': 'ProductionType'},
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'productions.screenshot': {
            'Meta': {'object_name': 'Screenshot'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'original_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'original_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'screenshots'", 'to': u"orm['productions.Production']"}),
            'source_download_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'standard_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'standard_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'standard_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'productions.soundtracklink': {
            'Meta': {'ordering': "['position']", 'object_name': 'SoundtrackLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'soundtrack_links'", 'to': u"orm['productions.Production']"}),
            'soundtrack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'appearances_as_soundtrack'", 'to': u"orm['productions.Production']"})
        }
    }

    complete_apps = ['productions']