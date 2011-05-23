from django.db import models
import re, os, datetime
from urlparse import urlparse
from fuzzy_date import FuzzyDate
from django.contrib.auth.models import User
from model_thumbnail import ModelWithThumbnails
from django.utils.encoding import StrAndUnicode
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from strip_markup import strip_markup

from treebeard.mp_tree import MP_Node
from taggit.managers import TaggableManager

# Create your models here.
class Platform(ModelWithThumbnails):
	name = models.CharField(max_length=255)
	intro_text = models.TextField(blank = True)
	
	photo = models.ImageField(
		null = True, blank = True,
		upload_to = (lambda i, f: Platform.random_path('platform_photos/original', f) ),
		width_field = 'photo_width', height_field = 'photo_height')
	photo_width = models.IntegerField(null = True, blank = True, editable=False)
	photo_height = models.IntegerField(null = True, blank = True, editable=False)
	
	thumbnail = models.ImageField(
		null = True, blank = True,
		upload_to = (lambda i, f: Platform.random_path('platform_photos/thumb', f) ),
		editable=False, width_field = 'thumbnail_width', height_field = 'thumbnail_height')
	thumbnail_width = models.IntegerField(null = True, blank = True, editable=False)
	thumbnail_height = models.IntegerField(null = True, blank = True, editable=False)
	
	def save(self, *args, **kwargs):
		if self.photo:
			Screenshot.generate_thumbnail(self.photo, self.thumbnail, (135, 90), crop = True)
		super(Platform, self).save(*args, **kwargs)
	
	def __unicode__(self):
		return self.name
	
	def random_active_groups(self):
		return Releaser.objects.raw('''
			SELECT * FROM (
				SELECT group_id AS id, group_name AS title, MAX(release_date) FROM (
				
					-- all groups named as authors of prods on this platform
					SELECT
						demoscene_releaser.id AS group_id,
						demoscene_releaser.name AS group_name,
						demoscene_production.release_date_date AS release_date
					FROM
						demoscene_production
						INNER JOIN demoscene_production_platforms ON (
							demoscene_production.id = demoscene_production_platforms.production_id
							AND demoscene_production_platforms.platform_id = %s
						)
						INNER JOIN demoscene_production_author_nicks ON (
							demoscene_production.id = demoscene_production_author_nicks.production_id
						)
						INNER JOIN demoscene_nick ON (
							demoscene_production_author_nicks.nick_id = demoscene_nick.id
						)
						INNER JOIN demoscene_releaser ON (
							demoscene_nick.releaser_id = demoscene_releaser.id
							AND is_group = 't'
						)
					WHERE
						demoscene_production.release_date_date IS NOT NULL
		
					UNION
		
					-- all groups named as author affiliations of prods on this platform
					SELECT
						demoscene_releaser.id AS group_id,
						demoscene_releaser.name AS group_name,
						demoscene_production.release_date_date AS release_date
					FROM
						demoscene_production
						INNER JOIN demoscene_production_platforms ON (
							demoscene_production.id = demoscene_production_platforms.production_id
							AND demoscene_production_platforms.platform_id = %s
						)
						INNER JOIN demoscene_production_author_affiliation_nicks ON (
							demoscene_production.id = demoscene_production_author_affiliation_nicks.production_id
						)
						INNER JOIN demoscene_nick ON (
							demoscene_production_author_affiliation_nicks.nick_id = demoscene_nick.id
						)
						INNER JOIN demoscene_releaser ON (
							demoscene_nick.releaser_id = demoscene_releaser.id
							AND is_group = 't'
						)
					WHERE
						demoscene_production.release_date_date IS NOT NULL
		
				) AS grps
				
				GROUP BY group_id, group_name
				ORDER BY MAX(release_date) DESC
				LIMIT 100
			) AS topgroups
			ORDER BY RANDOM()
			LIMIT 10;
		''', (self.id, self.id))
	class Meta:
		ordering = ['name']

class ProductionType(MP_Node):
	name = models.CharField(max_length=255)
	position = models.IntegerField(default = 0, help_text = "Position in which this should be ordered underneath its parent type (if not alphabetical)")
	internal_name = models.CharField(blank = True, max_length = 32, help_text = "Used to identify this prod type for special treatment in code - leave this alone!")
	
	node_order_by = ['position', 'name']
	
	def __unicode__(self):
		return self.name
	
	@staticmethod
	def music_types():
		try:
			music = ProductionType.objects.get(internal_name = 'music')
			return ProductionType.get_tree(music)
		except ProductionType.DoesNotExist:
			return ProductionType.objects.none()
	
	@staticmethod
	def graphic_types():
		try:
			graphics = ProductionType.objects.get(internal_name = 'graphics')
			return ProductionType.get_tree(graphics)
		except ProductionType.DoesNotExist:
			return ProductionType.objects.none()
	
	@staticmethod
	def featured_types():
		tree = ProductionType.get_tree()
		music_types = ProductionType.music_types()
		graphic_types = ProductionType.graphic_types()
		
		if music_types:
			tree = tree.exclude(id__in = music_types.values('pk'))
		if graphic_types:
			tree = tree.exclude(id__in = graphic_types.values('pk'))
		
		return tree

class Releaser(models.Model):
	external_site_ref_field_names = [
		'sceneid_user_id','slengpung_user_id','amp_author_id','csdb_author_id','nectarine_author_id',
		'bitjam_author_id','artcity_author_id','mobygames_author_id', 'asciiarena_author_id']
	
	name = models.CharField(max_length=255)
	is_group = models.BooleanField()
	notes = models.TextField(blank = True)
	
	sceneid_user_id = models.IntegerField(null = True, blank = True, verbose_name = 'SceneID / Pouet user ID')
	slengpung_user_id = models.IntegerField(null = True, blank = True, verbose_name = 'Slengpung user ID')
	amp_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'AMP author ID')
	csdb_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'CSDb author ID')
	nectarine_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'Nectarine author ID')
	bitjam_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'Bitjam author ID')
	artcity_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'ArtCity author ID')
	mobygames_author_id = models.IntegerField(null = True, blank = True, verbose_name = 'MobyGames author ID')
	asciiarena_author_id = models.CharField(blank = True, max_length = 32, verbose_name = 'AsciiArena author ID')
	demozoo0_id = models.IntegerField(null = True, blank = True, verbose_name = 'Demozoo v0 ID')
	
	location = models.CharField(max_length = 255, blank = True)
	country_code = models.CharField(max_length = 5, blank = True)
	latitude = models.FloatField(null = True, blank = True)
	longitude = models.FloatField(null = True, blank = True)
	woe_id = models.BigIntegerField(null = True, blank = True)
	
	first_name = models.CharField(max_length = 255, blank = True)
	show_first_name = models.BooleanField(default = True)
	surname = models.CharField(max_length = 255, blank = True)
	show_surname = models.BooleanField(default = True)
	real_name_note = models.TextField(default = '', blank = True, verbose_name = 'Permission note', help_text = "Details of any correspondence / decision about whether this name should be public")
	
	data_source = models.CharField(max_length = 32, blank = True, null = True)
	
	created_at = models.DateTimeField(auto_now_add = True)
	updated_at = models.DateTimeField()
	
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
		return [True for field in self.external_site_ref_field_names if self.__dict__[field]]
	
	def pouet_user_url(self):
		if self.sceneid_user_id:
			return "http://pouet.net/user.php?who=%s" % self.sceneid_user_id
	
	def slengpung_user_url(self):
		if self.slengpung_user_id:
			return "http://www.slengpung.com/v3/show_user.php?id=%s" % self.slengpung_user_id
	
	def amp_author_url(self):
		if self.amp_author_id:
			return "http://amp.dascene.net/detail.php?view=%s" % self.amp_author_id
	
	def csdb_author_url(self):
		if self.csdb_author_id:
			return "http://noname.c64.org/csdb/scener/?id=%s" % self.csdb_author_id
	
	def nectarine_author_url(self):
		if self.nectarine_author_id:
			return "http://www.scenemusic.net/demovibes/artist/%s/" % self.nectarine_author_id
	
	def bitjam_author_url(self):
		if self.bitjam_author_id:
			return "http://www.bitfellas.org/e107_plugins/radio/radio.php?search&q=%s&type=author&page=1" % self.bitjam_author_id
	
	def artcity_author_url(self):
		if self.artcity_author_id:
			return "http://artcity.bitfellas.org/index.php?a=artist&id=%s" % self.artcity_author_id
	
	def mobygames_author_url(self):
		if self.mobygames_author_id:
			return "http://www.mobygames.com/developer/sheet/view/developerId,%s/" % self.mobygames_author_id
	
	def asciiarena_author_url(self):
		if self.asciiarena_author_id:
			return "http://www.asciiarena.com/info_artist.php?artist=%s&sort_by=filename" % self.asciiarena_author_id
	
	def groups(self):
		return [membership.group for membership in self.group_memberships.select_related('group')]
	
	def current_groups(self):
		return [membership.group for membership in self.group_memberships.filter(is_current = True).select_related('group')]
	
	def members(self):
		return [membership.member for membership in self.member_memberships.select_related('member')]
	
	def name_with_affiliations(self):
		groups = self.current_groups()
		
		if groups:
			if sum([len(group.name) for group in groups]) >= 20:
				# abbreviate where possible
				group_names = [(group.abbreviation or group.name) for group in groups]
			else:
				# use full group names - not too long
				group_names = [group.name for group in groups]
			return "%s / %s" % (self.name, ' ^ '.join(group_names))
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
	
	@property
	def public_real_name(self):
		if self.first_name and self.show_first_name and self.surname and self.show_surname:
			return "%s %s" % (self.first_name, self.surname)
		elif self.first_name and self.show_first_name:
			return self.first_name
		elif self.surname and self.show_surname:
			return self.surname
		else:
			return None
	
	def real_name_available_to_show(self):
		return (self.first_name and self.show_first_name) or (self.surname and self.show_surname)
	
	def can_reveal_full_real_name(self):
		return (self.show_first_name and self.show_surname)
	
	@property
	def all_names_string(self):
		all_names = [nv.name for nv in NickVariant.objects.filter(nick__releaser = self)]
		return ', '.join(all_names)
	
	@property
	def all_affiliation_names_string(self):
		all_names = [nv.name for nv in NickVariant.objects.filter(nick__releaser__member_memberships__member = self)]
		return ', '.join(all_names)
	
	# Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
	# that should prevent its deletion
	def is_referenced(self):
		return (
			self.credits().count()
			or self.member_memberships.count() # A group with members can't be deleted, although a scener with groups can. Seems to make sense...
			or self.productions().count()
			or self.member_productions().count() )
	
	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)

class Nick(models.Model):
	releaser = models.ForeignKey(Releaser, related_name = 'nicks')
	name = models.CharField(max_length=255)
	abbreviation = models.CharField(max_length = 255, blank = True, help_text = "(optional - only if there's one that's actively being used. Don't just make one up!)")
	differentiator = models.CharField(max_length = 32, blank = True, help_text = "hint text to distinguish from other groups/sceners with the same name - e.g. platform or country")
	
	def __init__(self, *args, **kwargs):
		super(Nick, self).__init__(*args, **kwargs)
		self._has_written_nick_variant_list = False
		self._nick_variant_list = None
	
	def __unicode__(self):
		return self.name
	
	@staticmethod
	def from_id_and_name(id, name):
		if id == 'newgroup':
			releaser = Releaser(name = name, is_group = True, updated_at = datetime.datetime.now())
			releaser.save()
			return releaser.primary_nick
		elif id == 'newscener':
			releaser = Releaser(name = name, is_group = False, updated_at = datetime.datetime.now())
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
		groups = self.releaser.current_groups()
		
		if groups:
			if sum([len(group.name) for group in groups]) >= 20:
				# abbreviate where possible
				group_names = [(group.abbreviation or group.name) for group in groups]
			else:
				# use full group names - not too long
				group_names = [group.name for group in groups]
			return "%s / %s" % (self.name, ' ^ '.join(group_names))
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
	
	class Meta:
		unique_together = ("releaser","name")

class NickVariant(models.Model):
	nick = models.ForeignKey(Nick, related_name = 'variants')
	name = models.CharField(max_length = 255)
	
	def __unicode__(self):
		return self.name
	
	@staticmethod
	def autocomplete(initial_query, significant_whitespace = True, **kwargs):
		if significant_whitespace:
			# treat trailing whitespace as a required part of the name
			# (e.g. "Andromeda " will only match "Andromeda Software Development", not "Andromeda"
			query = initial_query
		else:
			query = initial_query.strip()
		
		# look for possible autocompletions; choose the top-ranked one and use that as the query
		autocompletions = NickVariant.autocompletion_search(query, limit = 1, **kwargs)
		try:
			result = autocompletions[0].name
			# return just the suffix to add; the caller will append this to the original query,
			# thus preserving capitalisation in exactly the way that iTunes doesn't.
			# (Ha, I rule.)
			return result[len(initial_query):]
		except IndexError: # no autocompletions available
			return ''
	
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
					select = SortedDict([
						('score', '''
							SELECT COUNT(*) FROM demoscene_membership
							INNER JOIN demoscene_releaser AS demogroup ON (demoscene_membership.group_id = demogroup.id)
							INNER JOIN demoscene_nick AS group_nick ON (demogroup.id = group_nick.releaser_id)
							INNER JOIN demoscene_nickvariant AS group_nickvariant ON (group_nick.id = group_nickvariant.nick_id)
							WHERE demoscene_membership.member_id = demoscene_releaser.id
							AND LOWER(group_nickvariant.name) IN %s
						'''),
						('is_exact_match', '''
							CASE WHEN LOWER(demoscene_nickvariant.name) = LOWER(%s) THEN 1 ELSE 0 END
						'''),
						('is_primary_nickvariant', '''
							CASE WHEN demoscene_nick.name = demoscene_nickvariant.name THEN 1 ELSE 0 END
						'''),
					]),
					select_params = (tuple(groups), query),
					order_by = ('-score','-is_exact_match','-is_primary_nickvariant','name')
				)
			elif members:
				nick_variants = nick_variants.extra(
					select = SortedDict([
						('score', '''
							SELECT COUNT(*) FROM demoscene_membership
							INNER JOIN demoscene_releaser AS member ON (demoscene_membership.member_id = member.id)
							INNER JOIN demoscene_nick AS member_nick ON (member.id = member_nick.releaser_id)
							INNER JOIN demoscene_nickvariant AS member_nickvariant ON (member_nick.id = member_nickvariant.nick_id)
							WHERE demoscene_membership.group_id = demoscene_releaser.id
							AND LOWER(member_nickvariant.name) IN %s
						'''),
						('is_exact_match', '''
							CASE WHEN LOWER(demoscene_nickvariant.name) = LOWER(%s) THEN 1 ELSE 0 END
						'''),
						('is_primary_nickvariant', '''
							CASE WHEN demoscene_nick.name = demoscene_nickvariant.name THEN 1 ELSE 0 END
						'''),
					]),
					select_params = (tuple(members), query),
					order_by = ('-score','-is_exact_match','-is_primary_nickvariant','name')
				)
			else:
				nick_variants = nick_variants.extra(
					select = SortedDict([
						('score', '0'),
						('is_exact_match', '''
							CASE WHEN LOWER(demoscene_nickvariant.name) = LOWER(%s) THEN 1 ELSE 0 END
						'''),
						('is_primary_nickvariant', '''
							CASE WHEN demoscene_nick.name = demoscene_nickvariant.name THEN 1 ELSE 0 END
						'''),
					]),
					select_params = (query,),
					order_by = ('-is_exact_match','-is_primary_nickvariant','name')
				)
			if limit:
				nick_variants = nick_variants[:limit]
			
			nick_variants = nick_variants.select_related('nick', 'nick__releaser')
		else:
			nick_variants = NickVariant.objects.none()
			
		return nick_variants

class Membership(models.Model):
	member = models.ForeignKey(Releaser, related_name = 'group_memberships')
	group = models.ForeignKey(Releaser, limit_choices_to = {'is_group': True}, related_name = 'member_memberships')
	is_current = models.BooleanField(default = True)
	data_source = models.CharField(max_length = 32, blank = True, null = True)
	
	def __unicode__(self):
		return "%s / %s" % (self.member.name, self.group.name)

SUPERTYPE_CHOICES = (
	('production', _('Production')), 
	('graphics', _('Graphics')),
	('music', _('Music')),
)

class Production(models.Model):
	title = models.CharField(max_length=255)
	platforms = models.ManyToManyField('Platform', related_name = 'productions', blank=True)
	supertype = models.CharField(max_length = 32, choices=SUPERTYPE_CHOICES)
	types = models.ManyToManyField('ProductionType', related_name = 'productions')
	author_nicks = models.ManyToManyField('Nick', related_name = 'productions', blank = True)
	author_affiliation_nicks = models.ManyToManyField('Nick', related_name = 'member_productions', blank=True, null=True)
	notes = models.TextField(blank = True)
	release_date_date = models.DateField(null = True, blank = True)
	release_date_precision = models.CharField(max_length = 1, blank = True)

	external_site_ref_field_names = ['pouet_id','csdb_id','bitworld_id']
	pouet_id = models.IntegerField(null = True, blank = True, verbose_name = 'Pouet ID')
	csdb_id = models.IntegerField(null = True, blank = True, verbose_name = 'CSDb ID')
	bitworld_id = models.IntegerField(null = True, blank = True, verbose_name = 'Bitworld ID')
	
	has_bonafide_edits = models.BooleanField(default = True, help_text = "True if this production has been updated through its own forms, as opposed to just compo results tables")
	created_at = models.DateTimeField(auto_now_add = True)
	updated_at = models.DateTimeField()
	
	tags = TaggableManager(blank=True)
	
	search_result_template = 'search/results/production.html'
	
	def save(self, *args, **kwargs):
		if self.id and not self.supertype:
			self.supertype = self.inferred_supertype
		return super(Production, self).save(*args, **kwargs)
	
	def __unicode__(self):
		return self.title
	
	def byline(self):
		return Byline(self.author_nicks.all(), self.author_affiliation_nicks.all())
	
	@property
	def byline_string(self):
		return unicode(self.byline())
	
	@property
	def inferred_supertype(self):
		try:
			prod_type = self.types.all()[0]
		except IndexError:
			return 'production'
		
		if prod_type in ProductionType.music_types():
			return 'music'
		elif prod_type in ProductionType.graphic_types():
			return 'graphics'
		else:
			return 'production'
	
	@models.permalink
	def get_absolute_url(self):
		if self.supertype == 'music':
			return ('demoscene.views.music.show', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('demoscene.views.graphics.show', [str(self.id)])
		else:
			return ('demoscene.views.productions.show', [str(self.id)])

	@models.permalink
	def get_absolute_edit_url(self):
		if self.supertype == 'music':
			return ('demoscene.views.music.edit', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('demoscene.views.graphics.edit', [str(self.id)])
		else:
			return ('demoscene.views.productions.edit', [str(self.id)])
	
	@models.permalink
	def get_edit_done_url(self):
		if self.supertype == 'music':
			return ('edit_music_done', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('edit_graphics_done', [str(self.id)])
		else:
			return ('edit_production_done', [str(self.id)])
	
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
		return [True for field in self.external_site_ref_field_names if self.__dict__[field]]
		
	def pouet_url(self):
		if self.pouet_id:
			return "http://pouet.net/prod.php?which=%s" % self.pouet_id
			
	def csdb_url(self):
		if self.csdb_id:
			return "http://noname.c64.org/csdb/release/?id=%s" % self.csdb_id
	
	def bitworld_url(self):
		if self.bitworld_id:
			return "http://bitworld.bitfellas.org/demo.php?id=%s" % self.bitworld_id
	
	def ordered_download_links(self):
		download_links = self.download_links.all()
		# reorder to put scene.org links first
		return [d for d in download_links if d.host_identifier() == 'sceneorg'] + \
			[d for d in download_links if d.host_identifier() != 'sceneorg']
	
	# whether this production is regarded as 'stable' in competition results editing;
	# i.e. it will not be deleted or have its details edited in response to actions
	# in the compo results editing interface
	def is_stable_for_competitions(self):
		return self.has_bonafide_edits or self.competition_placings.count() > 1
	
	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)

# encapsulates list of authors and affiliations
class Byline(StrAndUnicode):
	def __init__(self, authors = [], affiliations = []):
		self.author_nicks = authors
		self.affiliation_nicks = affiliations
	
	def __unicode__(self):
		authors_string = ' + '.join([nick.name for nick in self.author_nicks])
		if self.affiliation_nicks:
			affiliations_string = ' ^ '.join([nick.name for nick in self.affiliation_nicks])
			return "%s / %s" % (authors_string, affiliations_string)
		else:
			return authors_string
	
	def commit(self, production):
		from matched_nick_field import NickSelection
		
		author_nicks = []
		for nick in self.author_nicks:
			if isinstance(nick, NickSelection):
				author_nicks.append(nick.commit())
			else:
				author_nicks.append(nick)
		
		affiliation_nicks = []
		for nick in self.affiliation_nicks:
			if isinstance(nick, NickSelection):
				affiliation_nicks.append(nick.commit())
			else:
				affiliation_nicks.append(nick)
		
		production.author_nicks = author_nicks
		production.author_affiliation_nicks = affiliation_nicks
	
	@staticmethod
	def from_releaser_id(releaser_id):
		if releaser_id:
			try:
				return Byline([Releaser.objects.get(id = releaser_id).primary_nick])
			except Releaser.DoesNotExist:
				pass
		return Byline()

class DownloadLink(models.Model):
	production = models.ForeignKey(Production, related_name = 'download_links')
	url = models.CharField(max_length = 2048, verbose_name = 'download URL')
	
	def hostname(self):
		return urlparse(self.url).hostname
	
	def host_identifier(self):
		host = self.hostname()
		if host == 'ftp.amigascne.org':
			return 'amigascne'
		elif host == 'www.scene.org':
			return 'sceneorg'
		elif host == 'ftp.untergrund.net':
			return 'untergrund'
		else:
			return None

class Credit(models.Model):
	production = models.ForeignKey(Production, related_name = 'credits')
	nick = models.ForeignKey(Nick, related_name = 'credits')
	role = models.CharField(max_length = 255, blank = True)
	
	def __unicode__(self):
		return "%s - %s (%s)" % (
			self.production_id and self.production.title,
			self.nick_id and self.nick.name,
			self.role)

class Screenshot(ModelWithThumbnails):
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
			Screenshot.generate_thumbnail(self.original, self.thumbnail, (135, 90), crop = True)
			Screenshot.generate_thumbnail(self.original, self.standard, (400, 400), crop = False)
		
		# Save this photo instance
		super(Screenshot, self).save(*args, **kwargs)
	
	def __unicode__(self):
		return "%s - %s" % (self.production.title, self.original)

class PartySeries(models.Model):
	name = models.CharField(max_length = 255, unique = True)
	notes = models.TextField(blank = True)
	website = models.URLField(blank = True, verify_exists = False)
	twitter_username = models.CharField(max_length = 30, blank = True)
	pouet_party_id = models.IntegerField(null = True, blank = True, verbose_name = 'Pouet party ID')
	
	def __unicode__(self):
		return self.name
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.parties.show_series', [str(self.id)])
	
	@models.permalink
	def get_absolute_edit_url(self):
		return ('demoscene.views.parties.show_series', [str(self.id)])
	
	def has_any_external_links(self):
		return self.website or self.twitter_url or self.pouet_url
	
	def twitter_url(self):
		if self.twitter_username:
			return "http://twitter.com/%s" % self.twitter_username
	def pouet_url(self):
		if self.pouet_party_id:
			return "http://www.pouet.net/party.php?which=%s" % self.pouet_party_id
	
	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)
	
	class Meta:
		verbose_name_plural = "Party series"

class PartySeriesDemozoo0Reference(models.Model):
	party_series = models.ForeignKey(PartySeries, related_name = 'demozoo0_ids')
	demozoo0_id = models.IntegerField(null = True, blank = True, verbose_name = 'Demozoo v0 ID')

class Party(models.Model):
	party_series = models.ForeignKey(PartySeries, related_name = 'parties')
	name = models.CharField(max_length = 255, unique = True)
	tagline = models.CharField(max_length = 255, blank = True)
	start_date_date = models.DateField()
	start_date_precision = models.CharField(max_length = 1)
	end_date_date = models.DateField()
	end_date_precision = models.CharField(max_length = 1)
	
	location = models.CharField(max_length = 255, blank = True)
	country_code = models.CharField(max_length = 5, blank = True)
	latitude = models.FloatField(null = True, blank = True)
	longitude = models.FloatField(null = True, blank = True)
	woe_id = models.BigIntegerField(null = True, blank = True)
	
	notes = models.TextField(blank = True)
	
	external_site_ref_field_names = [
		'homepage', 'twitter_username', 'demoparty_net_url_fragment', 'slengpung_party_id',
		'pouet_party_id', 'bitworld_party_id', 'csdb_party_id', 'breaks_amiga_party_id',
		'scene_org_directory']
	homepage = models.URLField(blank = True, verify_exists = False)
	twitter_username = models.CharField(max_length = 30, blank = True)
	demoparty_net_url_fragment = models.CharField(max_length = 100, blank = True, verbose_name = 'demoparty.net URL fragment', help_text = 'e.g. evoke-2010')
	slengpung_party_id = models.IntegerField(null = True, blank = True, verbose_name = 'Slengpung party ID')
	pouet_party_id = models.IntegerField(null = True, blank = True, verbose_name = 'Pouet party ID')
	pouet_party_when = models.IntegerField(null = True, blank = True)
	bitworld_party_id = models.IntegerField(null = True, blank = True, verbose_name = 'Bitworld party ID')
	csdb_party_id = models.IntegerField(null = True, blank = True, verbose_name = 'CSDB party ID')
	breaks_amiga_party_id = models.IntegerField(null = True, blank = True, verbose_name = "Break's Amiga party ID")
	scene_org_directory = models.CharField(max_length = 255, blank = True, verbose_name = 'scene.org directory', help_text = 'e.g. /parties/1991/theparty91/')
	
	search_result_template = 'search/results/party.html'
	
	def __unicode__(self):
		return self.name
	
	@models.permalink
	def get_absolute_url(self):
		return ('demoscene.views.parties.show', [str(self.id)])
	
	@models.permalink
	def get_absolute_edit_url(self):
		return ('demoscene.views.parties.show', [str(self.id)])
	
	@property
	def suffix(self):
		series_name = self.party_series.name
		if series_name == self.name and self.start_date:
			return self.start_date.date.year
		else:
			return re.sub(r"^" + re.escape(series_name) + r"\s+", '', self.name)
	
	def _get_start_date(self):
		return FuzzyDate(self.start_date_date, self.start_date_precision)
	def _set_start_date(self, fuzzy_date):
		self.start_date_date = fuzzy_date.date
		self.start_date_precision = fuzzy_date.precision
	start_date = property(_get_start_date,_set_start_date)
	
	def _get_end_date(self):
		return FuzzyDate(self.end_date_date, self.end_date_precision)
	def _set_end_date(self, fuzzy_date):
		self.end_date_date = fuzzy_date.date
		self.end_date_precision = fuzzy_date.precision
	end_date = property(_get_end_date,_set_end_date)
	
	def random_screenshot(self):
		screenshots = Screenshot.objects.filter(production__competition_placings__competition__party = self)
		try:
			return screenshots.order_by('?')[0]
		except IndexError:
			return None
	
	def has_any_external_links(self):
		return [True for field in self.external_site_ref_field_names if self.__dict__[field]]
	
	def twitter_url(self):
		if self.twitter_username:
			return "http://twitter.com/%s" % self.twitter_username
	def demoparty_net_url(self):
		if self.demoparty_net_url_fragment:
			return "http://www.demoparty.net/%s/" % self.demoparty_net_url_fragment
	def slengpung_url(self):
		if self.slengpung_party_id:
			return "http://www.slengpung.com/v3/parties.php?id=%s&order=name" % self.slengpung_party_id
	def pouet_url(self):
		if self.pouet_party_id and self.pouet_party_when:
			return "http://www.pouet.net/party.php?which=%s&when=%s" % (self.pouet_party_id, self.pouet_party_when)
	def bitworld_url(self):
		if self.bitworld_party_id:
			return "http://bitworld.bitfellas.org/party.php?id=%s" % self.bitworld_party_id
	def csdb_url(self):
		if self.csdb_party_id:
			return "http://www.csdb.dk/event/?id=%s" % self.csdb_party_id
	def breaks_amiga_url(self):
		if self.breaks_amiga_party_id:
			return "http://arabuusimiehet.com/break/amiga/index.php?mode=party&partyid=%s" % self.breaks_amiga_party_id
	def scene_org_url(self):
		if self.scene_org_directory:
			return "http://www.scene.org/dir.php?dir=%s" % self.scene_org_directory
	
	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)
	
	class Meta:
		verbose_name_plural = "Parties"
		ordering = ("start_date_date",)

class Competition(models.Model):
	party = models.ForeignKey(Party, related_name = 'competitions')
	name = models.CharField(max_length = 255)
	
	def results(self):
		return self.placings.order_by('position')
	
	def __unicode__(self):
		try:
			return "%s %s" % (self.party.name, self.name)
		except Party.DoesNotExist:
			return "(unknown party) %s" % self.name

class CompetitionPlacing(models.Model):
	competition = models.ForeignKey(Competition, related_name = 'placings')
	production = models.ForeignKey(Production, related_name = 'competition_placings')
	ranking = models.CharField(max_length = 32, blank = True)
	position = models.IntegerField()
	score = models.CharField(max_length = 32, blank = True)
	
	def __unicode__(self):
		try:
			return self.production.__unicode__()
		except Production.DoesNotExist:
			return "(CompetitionPlacing)"

class AccountProfile(models.Model):
	user = models.ForeignKey(User, unique = True)
	sticky_edit_mode = models.BooleanField(help_text = "Stays in edit mode when browsing around, until you explicitly hit 'done'")
	edit_mode_active = models.BooleanField(editable = False)
	demozoo0_id = models.IntegerField(null = True, blank = True, verbose_name = 'Demozoo v0 ID')

class SoundtrackLink(models.Model):
	production = models.ForeignKey(Production, related_name = 'soundtrack_links')
	soundtrack = models.ForeignKey(Production, limit_choices_to = {'supertype': 'music'}, related_name = 'appearances_as_soundtrack')
	position = models.IntegerField()
	
	def __unicode__(self):
		return "%s on %s" % (self.soundtrack, self.production)
	
	class Meta:
		ordering = ['position']
