from django.db import models
import re

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
	
	def save(self, *args, **kwargs):
		# ensure that a Nick with matching name exists for this releaser
		super(Releaser, self).save(*args, **kwargs) # Call the "real" save() method
		nick, created = Nick.objects.get_or_create(releaser = self, name = self.name)
	
	def __unicode__(self):
		return self.name
	
	@property
	def primary_nick(self):
		# find the nick which matches this releaser by name
		# (will die loudly if one doesn't exist. So let's hope it does, eh?)
		return self.nicks.get(name = self.name)
	
	@property
	def alternative_nicks(self):
		# A queryset of all nicks except the primary one
		return self.nicks.exclude(name = self.name)

class Nick(models.Model):
	releaser = models.ForeignKey(Releaser, related_name = 'nicks')
	name = models.CharField(max_length=255)
	
	def __init__(self, *args, **kwargs):
		super(Nick, self).__init__(*args, **kwargs)
		self._has_written_nick_variant_list = False
		self._nick_variant_list = None
	
	def __unicode__(self):
		return self.name
	
	def get_nick_variant_list(self):
		if self._has_written_nick_variant_list:
			return self._nick_variant_list
		else:
			variant_names = [variant.name for variant in self.variants.exclude(name = self.name)]
			return ", ".join(variant_names)
	def set_nick_variant_list(self, new_list):
		self._nick_variant_list = new_list
		self._has_written_nick_variant_list = True
	nick_variant_list = property(get_nick_variant_list, set_nick_variant_list)
	
	def save(self, *args, **kwargs):
		# update releaser's name if it matches this nick's previous name
		if self.id is not None:
			old_name = Nick.objects.get(id=self.id).name
			super(Nick, self).save(*args, **kwargs) # Call the original save() method
			if (old_name == self.releaser.name) and (old_name != self.name):
				self.releaser.name = self.name
				self.releaser.save()
		else:
			super(Nick, self).save(*args, **kwargs) # Call the original save() method
			
		if kwargs.get('commit', True) and self._has_written_nick_variant_list:
			# update the nick variant list
			old_variant_names = [variant.name for variant in self.variants.all()]
			new_variant_names = re.split(r"\s*\,\s*", self._nick_variant_list)
			new_variant_names.append(self.name)
			
			for variant in self.variants.all():
				if variant.name not in new_variant_names:
					variant.delete()
			for variant_name in new_variant_names:
				if variant_name not in old_variant_names:
					variant = NickVariant(nick = self, name = variant_name)
					variant.save()

class NickVariant(models.Model):
	nick = models.ForeignKey(Nick, related_name = 'variants')
	name = models.CharField(max_length = 255)
	
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
