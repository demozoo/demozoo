# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('demoscene', '0110_add_index_notes_flag_to_production'),
    )

    def forwards(self, orm):
        # RENAME ALL THE THINGS
        db.rename_table('demoscene_productiontype', 'productions_productiontype')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='platform').update(app_label='productions')

        db.rename_table('demoscene_production', 'productions_production')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='production').update(app_label='productions')

        db.rename_table('demoscene_production_platforms', 'productions_production_platforms')
        db.rename_table('demoscene_production_types', 'productions_production_types')
        db.rename_table('demoscene_production_author_nicks', 'productions_production_author_nicks')
        db.rename_table('demoscene_production_author_affiliation_nicks', 'productions_production_author_affiliation_nicks')

        db.rename_table('demoscene_productiondemozoo0platform', 'productions_productiondemozoo0platform')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='productiondemozoo0platform').update(app_label='productions')

        db.rename_table('demoscene_productionblurb', 'productions_productionblurb')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='productionblurb').update(app_label='productions')

        db.rename_table('demoscene_credit', 'productions_credit')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='credit').update(app_label='productions')

        db.rename_table('demoscene_screenshot', 'productions_screenshot')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='screenshot').update(app_label='productions')

        db.rename_table('demoscene_soundtracklink', 'productions_soundtracklink')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='soundtracklink').update(app_label='productions')

        db.rename_table('demoscene_packmember', 'productions_packmember')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='packmember').update(app_label='productions')

        db.rename_table('demoscene_productionlink', 'productions_productionlink')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='demoscene', model='productionlink').update(app_label='productions')


    def backwards(self, orm):
        # UNRENAME ALL THE THINGS
        db.rename_table('productions_productiontype', 'demoscene_productiontype')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='platform').update(app_label='demoscene')

        db.rename_table('productions_production', 'demoscene_production')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='production').update(app_label='demoscene')

        db.rename_table('productions_production_platforms', 'demoscene_production_platforms')
        db.rename_table('productions_production_types', 'demoscene_production_types')
        db.rename_table('productions_production_author_nicks', 'demoscene_production_author_nicks')
        db.rename_table('productions_production_author_affiliation_nicks', 'demoscene_production_author_affiliation_nicks')

        db.rename_table('productions_productiondemozoo0platform', 'demoscene_productiondemozoo0platform')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='productiondemozoo0platform').update(app_label='demoscene')

        db.rename_table('productions_productionblurb', 'demoscene_productionblurb')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='productionblurb').update(app_label='demoscene')

        db.rename_table('productions_credit', 'demoscene_credit')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='credit').update(app_label='demoscene')

        db.rename_table('productions_screenshot', 'demoscene_screenshot')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='screenshot').update(app_label='demoscene')

        db.rename_table('productions_soundtracklink', 'demoscene_soundtracklink')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='soundtracklink').update(app_label='demoscene')

        db.rename_table('productions_packmember', 'demoscene_packmember')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='packmember').update(app_label='demoscene')

        db.rename_table('productions_productionlink', 'demoscene_productionlink')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='productions', model='productionlink').update(app_label='demoscene')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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