from django.db import models

class Country(models.Model):
	code = models.CharField(max_length=2, primary_key=True)
	name = models.CharField(max_length=200, unique=True, db_index=True)

	def __unicode__(self):
		return self.name
