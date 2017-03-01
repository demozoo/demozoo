# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Releaser.asciiarena_author_id'
        db.delete_column('demoscene_releaser', 'asciiarena_author_id')

        # Deleting field 'Releaser.sceneid_user_id'
        db.delete_column('demoscene_releaser', 'sceneid_user_id')

        # Deleting field 'Releaser.csdb_author_id'
        db.delete_column('demoscene_releaser', 'csdb_author_id')

        # Deleting field 'Releaser.slengpung_user_id'
        db.delete_column('demoscene_releaser', 'slengpung_user_id')

        # Deleting field 'Releaser.artcity_author_id'
        db.delete_column('demoscene_releaser', 'artcity_author_id')

        # Deleting field 'Releaser.zxdemo_id'
        db.delete_column('demoscene_releaser', 'zxdemo_id')

        # Deleting field 'Releaser.bitjam_author_id'
        db.delete_column('demoscene_releaser', 'bitjam_author_id')

        # Deleting field 'Releaser.amp_author_id'
        db.delete_column('demoscene_releaser', 'amp_author_id')

        # Deleting field 'Releaser.mobygames_author_id'
        db.delete_column('demoscene_releaser', 'mobygames_author_id')

        # Deleting field 'Releaser.nectarine_author_id'
        db.delete_column('demoscene_releaser', 'nectarine_author_id')


    def backwards(self, orm):
        
        # Adding field 'Releaser.asciiarena_author_id'
        db.add_column('demoscene_releaser', 'asciiarena_author_id', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True), keep_default=False)

        # Adding field 'Releaser.sceneid_user_id'
        db.add_column('demoscene_releaser', 'sceneid_user_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.csdb_author_id'
        db.add_column('demoscene_releaser', 'csdb_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.slengpung_user_id'
        db.add_column('demoscene_releaser', 'slengpung_user_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.artcity_author_id'
        db.add_column('demoscene_releaser', 'artcity_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.zxdemo_id'
        db.add_column('demoscene_releaser', 'zxdemo_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.bitjam_author_id'
        db.add_column('demoscene_releaser', 'bitjam_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.amp_author_id'
        db.add_column('demoscene_releaser', 'amp_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.mobygames_author_id'
        db.add_column('demoscene_releaser', 'mobygames_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Releaser.nectarine_author_id'
        db.add_column('demoscene_releaser', 'nectarine_author_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'demoscene.accountprofile': {
            'Meta': {'object_name': 'AccountProfile'},
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'edit_mode_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sticky_edit_mode': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'demoscene.competition': {
            'Meta': {'object_name': 'Competition'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competitions'", 'to': "orm['demoscene.Party']"}),
            'platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demoscene.Platform']", 'null': 'True'}),
            'production_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demoscene.ProductionType']", 'null': 'True'}),
            'shown_date_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'shown_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        },
        'demoscene.competitionplacing': {
            'Meta': {'object_name': 'CompetitionPlacing'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'placings'", 'to': "orm['demoscene.Competition']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'competition_placings'", 'to': "orm['demoscene.Production']"}),
            'ranking': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'score': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        },
        'demoscene.credit': {
            'Meta': {'object_name': 'Credit'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credits'", 'to': "orm['demoscene.Nick']"}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credits'", 'to': "orm['demoscene.Production']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'demoscene.downloadlink': {
            'Meta': {'object_name': 'DownloadLink'},
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'download_links'", 'to': "orm['demoscene.Production']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        },
        'demoscene.membership': {
            'Meta': {'object_name': 'Membership'},
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'member_memberships'", 'to': "orm['demoscene.Releaser']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'group_memberships'", 'to': "orm['demoscene.Releaser']"})
        },
        'demoscene.nick': {
            'Meta': {'unique_together': "(('releaser', 'name'),)", 'object_name': 'Nick'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'differentiator': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nicks'", 'to': "orm['demoscene.Releaser']"})
        },
        'demoscene.nickvariant': {
            'Meta': {'object_name': 'NickVariant'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'nick': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variants'", 'to': "orm['demoscene.Nick']"})
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
        'demoscene.partyexternallink': {
            'Meta': {'object_name': 'PartyExternalLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_links'", 'to': "orm['demoscene.Party']"})
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
        'demoscene.partyseriesdemozoo0reference': {
            'Meta': {'object_name': 'PartySeriesDemozoo0Reference'},
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party_series': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'demozoo0_ids'", 'to': "orm['demoscene.PartySeries']"})
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
        'demoscene.production': {
            'Meta': {'object_name': 'Production'},
            'author_affiliation_nicks': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'member_productions'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['demoscene.Nick']"}),
            'author_nicks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'productions'", 'blank': 'True', 'to': "orm['demoscene.Nick']"}),
            'bitworld_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'csdb_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'has_bonafide_edits': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'platforms': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'productions'", 'blank': 'True', 'to': "orm['demoscene.Platform']"}),
            'pouet_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'release_date_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_date_precision': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'scene_org_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'supertype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': "orm['demoscene.ProductionType']"}),
            'unparsed_byline': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'zxdemo_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'demoscene.productiondemozoo0platform': {
            'Meta': {'object_name': 'ProductionDemozoo0Platform'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'demozoo0_platforms'", 'to': "orm['demoscene.Production']"})
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
        'demoscene.releaser': {
            'Meta': {'object_name': 'Releaser'},
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_group': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'real_name_note': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'show_first_name': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'show_surname': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {}),
            'woe_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'demoscene.releaserexternallink': {
            'Meta': {'object_name': 'ReleaserExternalLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_links'", 'to': "orm['demoscene.Releaser']"})
        },
        'demoscene.screenshot': {
            'Meta': {'object_name': 'Screenshot'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'original_height': ('django.db.models.fields.IntegerField', [], {}),
            'original_width': ('django.db.models.fields.IntegerField', [], {}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'screenshots'", 'to': "orm['demoscene.Production']"}),
            'standard': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'standard_height': ('django.db.models.fields.IntegerField', [], {}),
            'standard_width': ('django.db.models.fields.IntegerField', [], {}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'thumbnail_height': ('django.db.models.fields.IntegerField', [], {}),
            'thumbnail_width': ('django.db.models.fields.IntegerField', [], {})
        },
        'demoscene.soundtracklink': {
            'Meta': {'object_name': 'SoundtrackLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'production': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'soundtrack_links'", 'to': "orm['demoscene.Production']"}),
            'soundtrack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'appearances_as_soundtrack'", 'to': "orm['demoscene.Production']"})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['demoscene']
