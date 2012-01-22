from django.db import models

class BlobField(models.Field):
	description = "Blob"
	def db_type(self):
		return 'bytea' # only valid for postgres!

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^blob_field.BlobField"])
