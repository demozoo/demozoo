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


class Admin2Code(models.Model):
	geonameid = models.PositiveIntegerField(primary_key=True)
	code = models.CharField(max_length=30)
	name = models.CharField(max_length=200)
	country = models.ForeignKey(Country, related_name="admins2")
	admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="admins2")

	class Meta:
		unique_together = (("country", "admin1", "name"),)

	def __unicode__(self):
		s = u"{}".format(self.name)
		if self.admin1 is not None:
			s = u"{}, {}".format(s, self.admin1.name)

		return u"{}, {}".format(s, self.country.name)


class Locality(models.Model):
	geonameid = models.PositiveIntegerField(primary_key=True)
	name = models.CharField(max_length=200, db_index=True)
	country = models.ForeignKey(Country, null=True, blank=True, related_name="localities")
	admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="localities")
	admin2 = models.ForeignKey(Admin2Code, null=True, blank=True, related_name="localities")
	latitude = models.DecimalField(max_digits=8, decimal_places=5)
	longitude = models.DecimalField(max_digits=8, decimal_places=5)
	feature_class = models.CharField(max_length=1)
	feature_code = models.CharField(max_length=10)
	population = models.BigIntegerField(null=True)

	def __unicode__(self):
		long_name = u"{}".format(self.name)
		if self.admin2 is not None:
			long_name = u"{}, {}".format(long_name, self.admin2.name)

		if self.admin1 is not None:
			long_name = u"{}, {}".format(long_name, self.admin1.name)

		return long_name

class AlternateName(models.Model):
	locality = models.ForeignKey(Locality, related_name="alternatenames")
	name = models.CharField(max_length=200, db_index=True)

	def __unicode__(self):
		return self.name
