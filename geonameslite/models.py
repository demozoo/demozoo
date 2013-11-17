from django.db import models


class Country(models.Model):
	code = models.CharField(max_length=2, primary_key=True)
	name = models.CharField(max_length=200, unique=True, db_index=True)

	def __unicode__(self):
		return self.name


class Admin1Code(models.Model):
	geonameid = models.PositiveIntegerField(primary_key=True)
	code = models.CharField(max_length=7)
	name = models.CharField(max_length=200)
	country = models.ForeignKey(Country, related_name="admins1")

	def __unicode__(self):
		return u'%s, %s' % (self.name, self.country.name)
