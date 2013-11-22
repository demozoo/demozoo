from django.db import models
from django.db.models import Q

import re


class Country(models.Model):
	code = models.CharField(max_length=2, primary_key=True)
	name = models.CharField(max_length=200, unique=True)

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
	name = models.CharField(max_length=200)
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

	@staticmethod
	def search(term, partial=False):
		term = term.strip()
		if not term:
			return Locality.objects.none()

		parts = re.split(r',\s*', term)

		if len(parts) == 1 and partial:
			alt_name_matches = list(AlternateName.objects.filter(name__istartswith=parts[0]).values_list('locality_id', flat=True).distinct())
			query = Q(name__istartswith=parts[0]) | Q(geonameid__in=alt_name_matches)
		else:
			alt_name_matches = list(AlternateName.objects.filter(name__iexact=parts[0]).values_list('locality_id', flat=True).distinct())
			query = Q(name__iexact=parts[0]) | Q(geonameid__in=alt_name_matches)
			if partial:
				qualifiers = parts[1:-1]
				query &= (
					Q(country__name__istartswith=parts[-1]) | Q(country__code__istartswith=parts[-1])
					| Q(admin1__name__istartswith=parts[-1])
					| Q(admin2__name__istartswith=parts[-1])
				)
			else:
				qualifiers = parts[1:]

			for qualifier in qualifiers:
				query &= (
					Q(country__name__iexact=parts[-1]) | Q(country__code__iexact=parts[-1])
					| Q(admin1__name__iexact=parts[-1])
					| Q(admin2__name__iexact=parts[-1])
				)

		return Locality.objects.filter(query).order_by('-population')

class AlternateName(models.Model):
	locality = models.ForeignKey(Locality, related_name="alternatenames")
	name = models.CharField(max_length=200)

	def __unicode__(self):
		return self.name
