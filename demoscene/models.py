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
	notes = models.TextField(blank = True)
	
	def save(self, *args, **kwargs):
		# ensure that a Nick with matching name exists for this releaser
		super(Releaser, self).save(*args, **kwargs) # Call the "real" save() method
		nick, created = Nick.objects.get_or_create(releaser = self, name = self.name)
	
	def __unicode__(self):
		return self.name
		
	@models.permalink
	def get_absolute_url(self):
		if self.is_group:
			return ('demoscene.views.groups.show', [str(self.id)])
		else:
			return ('demoscene.views.sceners.show', [str(self.id)])
	
	def productions(self):
		return Production.objects.filter(author_nicks__releaser = self)

	def member_productions(self):
		return Production.objects.filter(author_affiliation_nicks__releaser = self)
	
	def credits(self):
		return Credit.objects.filter(nick__releaser = self)
	
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
	
	@staticmethod
	def from_id_and_name(id, name):
		if id == 'newgroup':
			releaser = Releaser(name = name, is_group = True)
			releaser.save()
			return releaser.primary_nick
		elif id == 'newscener':
			releaser = Releaser(name = name, is_group = False)
			releaser.save()
			return releaser.primary_nick
		else:
			return Nick.objects.get(id = id)
	
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
			if not self._has_written_nick_variant_list:
				# force writing a nick variant list containing just the primary nick
				self._has_written_nick_variant_list = True
				self._nick_variant_list = ''
			
		if kwargs.get('commit', True) and self._has_written_nick_variant_list:
			# update the nick variant list
			old_variant_names = [variant.name for variant in self.variants.all()]
			new_variant_names = re.split(r"\s*\,\s*", self._nick_variant_list)
			new_variant_names.append(self.name)
			
			for variant in self.variants.all():
				if variant.name not in new_variant_names:
					variant.delete()
			for variant_name in new_variant_names:
				if variant_name and variant_name not in old_variant_names:
					variant = NickVariant(nick = self, name = variant_name)
					variant.save()
					
			self._has_written_nick_variant_list = False

class NickVariant(models.Model):
	nick = models.ForeignKey(Nick, related_name = 'variants')
	name = models.CharField(max_length = 255)
	
	def __unicode__(self):
		return self.name
	
	@staticmethod
	def autocompletion_search(query, **kwargs):
		limit = kwargs.get('limit')
		exact = kwargs.get('exact', False)
		groups_only = kwargs.get('groups_only', False)
		sceners_only = kwargs.get('sceners_only', False)
		
		groups = [name.lower() for name in kwargs.get('groups', [])]
		members = [name.lower() for name in kwargs.get('members', [])]
		
		if query:
			if exact:
				nick_variants = NickVariant.objects.filter(name__iexact = query)
			else:
				nick_variants = NickVariant.objects.filter(name__istartswith = query)
			
			if groups_only:
				nick_variants = nick_variants.filter(nick__releaser__is_group = True)
			elif sceners_only:
				nick_variants = nick_variants.filter(nick__releaser__is_group = False)
			else:
				# nasty hack to ensure that we're joining on releaser, for the 'groups' subquery
				nick_variants = nick_variants.filter(nick__releaser__is_group__in = [True, False])
			
			if groups:
				nick_variants = nick_variants.extra(
					select = {
						'score': '''
							SELECT COUNT(*) FROM demoscene_releaser_groups
							INNER JOIN demoscene_releaser AS demogroup ON (demoscene_releaser_groups.to_releaser_id = demogroup.id)
							INNER JOIN demoscene_nick AS group_nick ON (demogroup.id = group_nick.releaser_id)
							INNER JOIN demoscene_nickvariant AS group_nickvariant ON (group_nick.id = group_nickvariant.nick_id)
							WHERE demoscene_releaser_groups.from_releaser_id = demoscene_releaser.id
							AND LOWER(group_nickvariant.name) IN %s
						'''
					},
					select_params = (tuple(groups), ),
					order_by = ('-score','name')
				)
			elif members:
				nick_variants = nick_variants.extra(
					select = {
						'score': '''
							SELECT COUNT(*) FROM demoscene_releaser_groups
							INNER JOIN demoscene_releaser AS member ON (demoscene_releaser_groups.from_releaser_id = member.id)
							INNER JOIN demoscene_nick AS member_nick ON (member.id = member_nick.releaser_id)
							INNER JOIN demoscene_nickvariant AS member_nickvariant ON (member_nick.id = member_nickvariant.nick_id)
							WHERE demoscene_releaser_groups.to_releaser_id = demoscene_releaser.id
							AND LOWER(member_nickvariant.name) IN %s
						'''
					},
					select_params = (tuple(members), ),
					order_by = ('-score','name')
				)
			else:
				nick_variants = nick_variants.extra(
					select = {'score': '0'},
					order_by = ('name',)
				)
			if limit:
				nick_variants = nick_variants[:limit]
		else:
			nick_variants = NickVariant.objects.none()
			
		return nick_variants

class Production(models.Model):
	title = models.CharField(max_length=255)
	platforms = models.ManyToManyField('Platform', related_name = 'productions')
	types = models.ManyToManyField('ProductionType', related_name = 'productions')
	author_nicks = models.ManyToManyField('Nick', related_name = 'productions')
	author_affiliation_nicks = models.ManyToManyField('Nick', related_name = 'member_productions', blank=True, null=True)
	notes = models.TextField(blank = True)
	
	def __unicode__(self):
		return self.title
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.productions.show', [str(self.id)])
		
	def byline(self):
		author_nicks = self.author_nicks.all()
		affiliation_nicks = self.author_affiliation_nicks.all()
		
		authors_string = ' + '.join([nick.name for nick in author_nicks])
		if affiliation_nicks:
			affiliations_string = ' ^ '.join([nick.name for nick in affiliation_nicks])
			return "%s / %s" % (authors_string, affiliations_string)
		else:
			return authors_string

class DownloadLink(models.Model):
	production = models.ForeignKey(Production, related_name = 'download_links')
	url = models.CharField(max_length = 2048)

class Credit(models.Model):
	production = models.ForeignKey(Production, related_name = 'credits')
	nick = models.ForeignKey(Nick, related_name = 'credits')
	role = models.CharField(max_length = 255, blank = True)
	
	def __unicode__(self):
		return "%s - %s (%s)" % (self.production.title, self.nick.name, self.role)

class PartySeries(models.Model):
	name = models.CharField(max_length = 255)
	
	def __unicode__(self):
		return self.name
	
	def parties_by_date(self):
		return self.parties.order_by('start_date') # TODO: can this be done as a native ordering on the parties relation instead?
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.parties.show_series', [str(self.id)])
	
	class Meta:
		verbose_name_plural = "Party series"

class Party(models.Model):
	party_series = models.ForeignKey(PartySeries, related_name = 'parties')
	name = models.CharField(max_length = 255)
	start_date = models.DateField()
	end_date = models.DateField()
	
	def __unicode__(self):
		return self.name
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.parties.show', [str(self.id)])
	
	class Meta:
		verbose_name_plural = "Parties"

class Competition(models.Model):
	party = models.ForeignKey(Party, related_name = 'competitions')
	name = models.CharField(max_length = 255)
	
	def results(self):
		return self.placings.order_by('position')
	
	def __unicode__(self):
		return "%s %s" % (self.party.name, self.name)

class CompetitionPlacing(models.Model):
	competition = models.ForeignKey(Competition, related_name = 'placings')
	production = models.ForeignKey(Production, related_name = 'competition_placings')
	ranking = models.CharField(max_length = 32, blank = True)
	position = models.IntegerField()
	score = models.CharField(max_length = 32, blank = True)
	
	def __unicode__(self):
		return self.production.__unicode__()
	