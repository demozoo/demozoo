# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Edit'
        db.create_table(u'editlog_edit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='edits', to=orm['auth.User'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('admin_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('detail', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'editlog', ['Edit'])

        # Adding model 'EditedItem'
        db.create_table(u'editlog_editeditem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('edit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='edited_items', to=orm['editlog.Edit'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('item_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='edited_items', to=orm['contenttypes.ContentType'])),
            ('item_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'editlog', ['EditedItem'])


    def backwards(self, orm):
        # Deleting model 'Edit'
        db.delete_table(u'editlog_edit')

        # Deleting model 'EditedItem'
        db.delete_table(u'editlog_editeditem')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'editlog.edit': {
            'Meta': {'object_name': 'Edit'},
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'admin_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'detail': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edits'", 'to': u"orm['auth.User']"})
        },
        u'editlog.editeditem': {
            'Meta': {'object_name': 'EditedItem'},
            'edit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edited_items'", 'to': u"orm['editlog.Edit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edited_items'", 'to': u"orm['contenttypes.ContentType']"}),
            'item_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['editlog']