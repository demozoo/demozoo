from django.db import models
import re, uuid, os
from fuzzy_date import FuzzyDate
from django.contrib.auth.models import User

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
	external_site_ref_field_names = ['sceneid_user_id','slengpung_user_id','amp_author_id','csdb_author_id','nectarine_author_id','bitjam_author_id','artcity_author_id','mobygames_author_id']
	
	name = models.CharField(max_length=255)
	is_group = models.BooleanField()
	groups = models.ManyToManyField('Releaser',
		limit_choices_to = {'is_group': True}, related_name = 'members')
	notes = models.TextField(blank = True)
	
	sceneid_user_id = models.IntegerField(null = True, blank = True, verbose_name = 'SceneID / Pouet user ID')
	slengpung_user_id = models.IntegerField(null = True, blank = True, verbose_name = 'Slengpung user ID')
	amp_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'AMP author ID')
	csdb_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'CSDb author ID')
	nectarine_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'Nectarine author ID')
	bitjam_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'Bitjam author ID')
	artcity_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'ArtCity author ID')
	mobygames_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'MobyGames author ID')
	
	location = models.CharField(max_length = 255, blank = True)
	country_code = models.CharField(max_length = 5, blank = True)
	latitude = models.FloatField(null = True, blank = True)
	longitude = models.FloatField(null = True, blank = True)
	woe_id = models.BigIntegerField(null = True, blank = True)
	
	first_name = models.CharField(max_length = 255, blank = True)
	surname = models.CharField(max_length = 255, blank = True)
	
	def save(self, *args, **kwargs):
		# ensure that a Nick with matching name exists for this releaser
		super(Releaser, self).save(*args, **kwargs) # Call the "real" save() method
		nick, created = Nick.objects.get_or_create(releaser = self, name = self.name)
	
	def __unicode__(self):
		return self.name
		
	def search_result_template(self):
		return 'search/results/group.html' if self.is_group else 'search/results/scener.html'
		
	@models.permalink
	def get_absolute_url(self):
		if self.is_group:
			return ('demoscene.views.groups.show', [str(self.id)])
		else:
			return ('demoscene.views.sceners.show', [str(self.id)])

	@models.permalink
	def get_absolute_edit_url(self):
		if self.is_group:
			return ('demoscene.views.groups.edit', [str(self.id)])
		else:
			return ('demoscene.views.sceners.edit', [str(self.id)])
	
	def productions(self):
		return Production.objects.filter(author_nicks__releaser = self)

	def member_productions(self):
		return Production.objects.filter(author_affiliation_nicks__releaser = self)
	
	def credits(self):
		return Credit.objects.filter(nick__releaser = self)
	
	def has_any_external_links(self):
		return [True for field in self.external_site_ref_field_names if self.__dict__[field] != None]
	
	def pouet_user_url(self):
		if self.sceneid_user_id:
			return "http://pouet.net/user.php?who=%s" % self.sceneid_user_id
		else:
			return None
	
	def slengpung_user_url(self):
		if self.slengpung_user_id:
			return "http://www.slengpung.com/v3/show_user.php?id=%s" % self.slengpung_user_id
		else:
			return None
	
	def amp_author_url(self):
		if self.amp_author_id:
			return "http://amp.dascene.net/detail.php?view=%s" % self.amp_author_id
		else:
			return None
	
	def csdb_author_url(self):
		if self.csdb_author_id:
			return "http://noname.c64.org/csdb/scener/?id=%s" % self.csdb_author_id
		else:
			return None
	
	def nectarine_author_url(self):
		if self.nectarine_author_id:
			return "http://www.scenemusic.net/demovibes/artist/%s/" % self.nectarine_author_id
		else:
			return None
	
	def bitjam_author_url(self):
		if self.bitjam_author_id:
			return "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1" % self.bitjam_author_id
		else:
			return None
	
	def artcity_author_url(self):
		if self.artcity_author_id:
			return "http://artcity.bitfellas.org/index.php?a=artist&id=%s" % self.artcity_author_id
		else:
			return None
	
	def mobygames_author_url(self):
		if self.mobygames_author_id:
			return "http://www.mobygames.com/developer/sheet/view/developerId,%s/" % self.mobygames_author_id
		else:
			return None
	
	def name_with_affiliations(self):
		groups = [group.name for group in self.groups.all()]
		if groups:
			return "%s / %s" % (self.name, ' ^ '.join(groups))
		else:
			return self.name
	
	@property
	def primary_nick(self):
		# find the nick which matches this releaser by name
		# (will die loudly if one doesn't exist. So let's hope it does, eh?)
		return self.nicks.get(name = self.name)
	
	@property
	def abbreviation(self):
		return self.primary_nick.abbreviation
	
	@property
	def alternative_nicks(self):
		# A queryset of all nicks except the primary one
		return self.nicks.exclude(name = self.name)
	
	@property
	def real_name(self):
		if self.first_name or self.surname:
			return "%s %s" % (self.first_name, self.surname)
		else:
			return None
	
	# Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
	# that should prevent its deletion
	def is_referenced(self):
		return (
			self.credits().count()
			or self.members.count() # A group with members can't be deleted, although a scener with groups can. Seems to make sense...
			or self.productions().count()
			or self.member_productions().count() )

class Nick(models.Model):
	releaser = models.ForeignKey(Releaser, related_name = 'nicks')
	name = models.CharField(max_length=255)
	abbreviation = models.CharField(max_length = 255, blank = True, help_text = "(optional - only if there's one that's actively being used. Don't just make one up!)")
	
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
			variant_names = [variant.name for variant in self.variants.exclude(name__in = [self.name, self.abbreviation])]
			return ", ".join(variant_names)
	def set_nick_variant_list(self, new_list):
		self._nick_variant_list = new_list
		self._has_written_nick_variant_list = True
	nick_variant_list = property(get_nick_variant_list, set_nick_variant_list)
	
	@property
	def nick_variant_and_abbreviation_list(self):
		variant_names = [variant.name for variant in self.variants.exclude(name = self.name)]
		return ", ".join(variant_names)
	
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
				# force writing a nick variant list containing just the primary nick (and abbreviation if specified)
				self._has_written_nick_variant_list = True
				self._nick_variant_list = ''
			
		if kwargs.get('commit', True) and self._has_written_nick_variant_list:
			# update the nick variant list
			old_variant_names = [variant.name for variant in self.variants.all()]
			new_variant_names = re.split(r"\s*\,\s*", self._nick_variant_list)
			new_variant_names.append(self.name)
			if self.abbreviation:
				new_variant_names.append(self.abbreviation)
			
			for variant in self.variants.all():
				if variant.name not in new_variant_names:
					variant.delete()
			for variant_name in new_variant_names:
				if variant_name and variant_name not in old_variant_names:
					variant = NickVariant(nick = self, name = variant_name)
					variant.save()
					
			self._has_written_nick_variant_list = False
	
	def name_with_affiliations(self):
		groups = [group.name for group in self.releaser.groups.all()]
		if groups:
			return "%s / %s" % (self.name, ' ^ '.join(groups))
		else:
			return self.name
	
	# Determine whether or not this nick is referenced in any external records (credits, authorships etc);
	# if not, it's safe to delete
	def is_referenced(self):
		return (
			self.releaser.name == self.name
			or self.credits.count()
			or self.productions.count()
			or self.member_productions.count() )

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
	release_date_date = models.DateField(null = True, blank = True)
	release_date_precision = models.CharField(max_length = 1, blank = True)

	external_site_ref_field_names = ['pouet_id','csdb_id','bitworld_id']
	pouet_id = models.IntegerField(null = True, blank = True, verbose_name = 'Pouet ID')
	csdb_id = models.IntegerField(null = True, blank = True, verbose_name = 'CSDb ID')
	bitworld_id = models.IntegerField(null = True, blank = True, verbose_name = 'Bitworld ID')
	
	search_result_template = 'search/results/production.html'
	
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
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.productions.show', [str(self.id)])

	@models.permalink
	def get_absolute_edit_url(self):
		return ('demoscene.views.productions.edit', [str(self.id)])
	
	def _get_release_date(self):
		if self.release_date_date and self.release_date_precision:
			return FuzzyDate(self.release_date_date, self.release_date_precision)
		else:
			return None
	def _set_release_date(self, fuzzy_date):
		if fuzzy_date:
			self.release_date_date = fuzzy_date.date
			self.release_date_precision = fuzzy_date.precision
		else:
			self.release_date_date = None
			self.release_date_precision = ''
	release_date = property(_get_release_date,_set_release_date)
	
	def has_any_external_links(self):
		return [True for field in self.external_site_ref_field_names if self.__dict__[field] != None]
		
	def pouet_url(self):
		if self.pouet_id:
			return "http://pouet.net/prod.php?which=%s" % self.pouet_id
		else:
			return None
			
	def csdb_url(self):
		if self.csdb_id:
			return "http://noname.c64.org/csdb/release/?id=%s" % self.csdb_id
		else:
			return None
	
	def bitworld_url(self):
		if self.bitworld_id:
			return "http://bitworld.bitfellas.org/demo.php?id=%s" % self.bitworld_id
		else:
			return None

class DownloadLink(models.Model):
	production = models.ForeignKey(Production, related_name = 'download_links')
	url = models.CharField(max_length = 2048, verbose_name = 'download URL')

class Credit(models.Model):
	production = models.ForeignKey(Production, related_name = 'credits')
	nick = models.ForeignKey(Nick, related_name = 'credits')
	role = models.CharField(max_length = 255, blank = True)
	
	def __unicode__(self):
		return "%s - %s (%s)" % (self.production.title, self.nick.name, self.role)

class Screenshot(models.Model):
	
	@staticmethod
	def random_path(prefix, filepath):
		hex = uuid.uuid4().hex;
		filename = os.path.basename(filepath)
		filename_root, filename_ext = os.path.splitext(filename)
		return prefix + '/' + hex[0] + '/' + hex[1] + '/' + hex[2:] + filename_ext
	
	production = models.ForeignKey(Production, related_name = 'screenshots')
	original = models.ImageField(
		upload_to = (lambda i, f: Screenshot.random_path('screenshots/original', f) ),
		verbose_name = 'image file', width_field = 'original_width', height_field = 'original_height')
	original_width = models.IntegerField()
	original_height = models.IntegerField()
	
	thumbnail = models.ImageField(
		upload_to = (lambda i, f: Screenshot.random_path('screenshots/thumb', f) ),
		editable=False, width_field = 'thumbnail_width', height_field = 'thumbnail_height')
	thumbnail_width = models.IntegerField()
	thumbnail_height = models.IntegerField()
	
	standard = models.ImageField(
		upload_to = (lambda i, f: Screenshot.random_path('screenshots/standard', f) ),
		editable=False, width_field = 'standard_width', height_field = 'standard_height')
	standard_width = models.IntegerField()
	standard_height = models.IntegerField()
	
	def save(self, *args, **kwargs):
		if not self.id:
			from model_thumbnail import generate_thumbnail
			generate_thumbnail(self.original, self.thumbnail, (135, 90), crop = True)
			generate_thumbnail(self.original, self.standard, (400, 400), crop = False)
		
		# Save this photo instance
		super(Screenshot, self).save(*args, **kwargs)
	
	def __unicode__(self):
		return "%s - %s" % (self.production.title, self.original)

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
	
	search_result_template = 'search/results/party.html'
	
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

class AccountProfile(models.Model):
	user = models.ForeignKey(User, unique = True)
	sticky_edit_mode = models.BooleanField(help_text = "Stays in edit mode when browsing around, until you explicitly hit 'done'")
	edit_mode_active = models.BooleanField(editable = False)
