# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SceneID'
        db.create_table(u'demoscene_sceneid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('sceneid', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('demoscene', ['SceneID'])

    def backwards(self, orm):
        # Deleting model 'SceneID'
        db.delete_table(u'demoscene_sceneid')



    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'demoscene.accountprofile': {
            'Meta': {'ordering': "['user__username']", 'object_name': 'AccountProfile'},
            'demozoo0_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'demoscene.sceneid': {
            'Meta': {'object_name': 'SceneID'},
            'sceneid': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'demoscene.captchaquestion': {
            'Meta': {'object_name': 'CaptchaQuestion'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {})
        },
        u'demoscene.edit': {
            'Meta': {'object_name': 'Edit', 'index_together': "[['focus_content_type', 'focus_object_id'], ['focus2_content_type', 'focus2_object_id']]"},
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'admin_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'focus2_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'edits_as_focus2'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'focus2_object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'focus_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edits'", 'to': u"orm['contenttypes.ContentType']"}),
            'focus_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'demoscene.membership': {
            'Meta': {'object_name': 'Membership'},
            'data_source': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'member_memberships'", 'to': u"orm['demoscene.Releaser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'group_memberships'", 'to': u"orm['demoscene.Releaser']"})
        },
        u'demoscene.nick': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('releaser', 'name'),)", 'object_name': 'Nick'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'differentiator': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nicks'", 'to': u"orm['demoscene.Releaser']"})
        },
        u'demoscene.nickvariant': {
            'Meta': {'ordering': "['name']", 'object_name': 'NickVariant'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'nick': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variants'", 'to': u"orm['demoscene.Nick']"})
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
            'is_group': ('django.db.models.fields.BooleanField', [], {'db_index': 'True'}),
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
        u'demoscene.releaserexternallink': {
            'Meta': {'ordering': "['link_class']", 'unique_together': "(('link_class', 'parameter', 'releaser'),)", 'object_name': 'ReleaserExternalLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_class': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'releaser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_links'", 'to': u"orm['demoscene.Releaser']"})
        },
        u'demoscene.tagdescription': {
            'Meta': {'object_name': 'TagDescription'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'tag': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'description'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['taggit.Tag']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['demoscene']