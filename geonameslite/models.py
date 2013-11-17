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
