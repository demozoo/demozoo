from django.db import models

# Create your models here.
class Platform(models.Model):
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.name

class ProductionType(models.Model):
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.name

class Releaser(models.Model):
	name = models.CharField(max_length=255)
	is_group = models.BooleanField()
	groups = models.ManyToManyField('Releaser',
		limit_choices_to = {'is_group': True}, related_name = 'members')
	
	def __unicode__(self):
		return self.name

class Nick(models.Model):
	releaser = models.ForeignKey(Releaser, related_name = 'nicks')
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.name

class Production(models.Model):
	title = models.CharField(max_length=255)
	platforms = models.ManyToManyField('Platform', related_name = 'productions')
	types = models.ManyToManyField('ProductionType', related_name = 'productions')
	
	def __unicode__(self):
		return self.title

class DownloadLink(models.Model):
	production = models.ForeignKey(Production, related_name = 'download_links')
	url = models.CharField(max_length = 2048)
