from django.db import models
from django.db.models import Q

import re
import datetime
import uuid
import os
from fuzzy_date import FuzzyDate
from django.contrib.auth.models import User
from model_thumbnail import ModelWithThumbnails
from django.utils.encoding import StrAndUnicode
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from strip_markup import strip_markup
from demoscene.utils import groklinks
from prefetch_snooping import ModelWithPrefetchSnooping

from treebeard.mp_tree import MP_Node
from taggit.managers import TaggableManager
from unidecode import unidecode
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


DATE_PRECISION_CHOICES = [
	('d', 'Day'),
	('m', 'Month'),
	('y', 'Year'),
]

def random_path(prefix, filepath):
	hex = uuid.uuid4().hex;
	filename = os.path.basename(filepath)
	filename_root, filename_ext = os.path.splitext(filename)
	return prefix + '/' + hex[0] + '/' + hex[1] + '/' + hex[2:] + filename_ext

class Platform(ModelWithThumbnails):
	name = models.CharField(max_length=255)
	intro_text = models.TextField(blank=True)

	photo = models.ImageField(
		null=True, blank=True,
		upload_to=(lambda i, f: random_path('platform_photos/original', f)),
		width_field='photo_width', height_field='photo_height')
	photo_width = models.IntegerField(null=True, blank=True, editable=False)
	photo_height = models.IntegerField(null=True, blank=True, editable=False)

	thumbnail = models.ImageField(
		null=True, blank=True,
		upload_to=(lambda i, f: random_path('platform_photos/thumb', f)),
		editable=False, width_field='thumbnail_width', height_field='thumbnail_height')
	thumbnail_width = models.IntegerField(null=True, blank=True, editable=False)
	thumbnail_height = models.IntegerField(null=True, blank=True, editable=False)

	def save(self, *args, **kwargs):
		if self.photo:
			Platform.generate_thumbnail(self.photo, self.thumbnail, (135, 90), crop=True)
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
	position = models.IntegerField(default=0, help_text="Position in which this should be ordered underneath its parent type (if not alphabetical)")
	internal_name = models.CharField(blank=True, max_length=32, help_text="Used to identify this prod type for special treatment in code - leave this alone!")

	node_order_by = ['position', 'name']

	def __unicode__(self):
		return self.name

	@staticmethod
	def music_types():
		try:
			music = ProductionType.objects.get(internal_name='music')
			return ProductionType.get_tree(music)
		except ProductionType.DoesNotExist:
			return ProductionType.objects.none()

	@staticmethod
	def graphic_types():
		try:
			graphics = ProductionType.objects.get(internal_name='graphics')
			return ProductionType.get_tree(graphics)
		except ProductionType.DoesNotExist:
			return ProductionType.objects.none()

	@staticmethod
	def featured_types():
		tree = ProductionType.get_tree()
		music_types = ProductionType.music_types()
		graphic_types = ProductionType.graphic_types()

		if music_types:
			tree = tree.exclude(id__in=music_types.values('pk'))
		if graphic_types:
			tree = tree.exclude(id__in=graphic_types.values('pk'))

		return tree

	@property
	def supertype(self):
		if self in ProductionType.music_types():
			return 'music'
		elif self in ProductionType.graphic_types():
			return 'graphics'
		else:
			return 'production'


class Releaser(ModelWithPrefetchSnooping, models.Model):
	name = models.CharField(max_length=255)
	is_group = models.BooleanField()
	notes = models.TextField(blank=True)

	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')

	location = models.CharField(max_length=255, blank=True)
	country_code = models.CharField(max_length=5, blank=True)
	latitude = models.FloatField(null=True, blank=True)
	longitude = models.FloatField(null=True, blank=True)
	woe_id = models.BigIntegerField(null=True, blank=True)
	geonames_id = models.BigIntegerField(null=True, blank=True)

	first_name = models.CharField(max_length=255, blank=True)
	show_first_name = models.BooleanField(default=True)
	surname = models.CharField(max_length=255, blank=True)
	show_surname = models.BooleanField(default=True)
	real_name_note = models.TextField(default='', blank=True, verbose_name='Permission note', help_text="Details of any correspondence / decision about whether this name should be public")

	data_source = models.CharField(max_length=32, blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField()

	def save(self, *args, **kwargs):
		# ensure that a Nick with matching name exists for this releaser
		super(Releaser, self).save(*args, **kwargs)  # Call the "real" save() method
		nick, created = Nick.objects.get_or_create(releaser=self, name=self.name)

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

	def get_absolute_edit_url(self):
		return self.get_absolute_url()

	@models.permalink
	def get_history_url(self):
		if self.is_group:
			return ('demoscene.views.groups.history', [str(self.id)])
		else:
			return ('demoscene.views.sceners.history', [str(self.id)])

	def productions(self):
		return Production.objects.filter(author_nicks__releaser=self)

	def member_productions(self):
		# Member productions are those which list this group in the 'affiliations' portion of the byline,
		# OR the author is a SUBGROUP of this group (regardless of whether this parent group is named as an affiliation).

		subgroup_ids = self.member_memberships.filter(member__is_group=True).values_list('member_id', flat=True)

		return Production.objects.filter(
			Q(author_affiliation_nicks__releaser=self)
			| Q(author_nicks__releaser__in=subgroup_ids)
		).distinct()

	def credits(self):
		return Credit.objects.select_related('nick').filter(nick__releaser=self)

	def groups(self):
		return [membership.group for membership in self.group_memberships.select_related('group').order_by('group__name')]

	def current_groups(self):
		if self.has_prefetched('group_memberships'):
			# do the is_current filter in Python to avoid another SQL query
			return [
				membership.group
				for membership in self.group_memberships.all()
				if membership.is_current
			]
		else:
			return [membership.group for membership in self.group_memberships.filter(is_current=True).select_related('group').order_by('group__name')]

	def members(self):
		return [membership.member for membership in self.member_memberships.select_related('member').order_by('member__name')]

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
		if self.has_prefetched('nicks'):
			# filter the nicks list in Python to avoid another SQL query
			matching_nicks = [n for n in self.nicks.all() if n.name == self.name]
			if not matching_nicks:
				raise Nick.DoesNotExist()
			elif len(matching_nicks) > 1:
				raise Nick.MultipleObjectsReturned()
			else:
				return matching_nicks[0]
		else:
			# find the nick which matches this releaser by name
			# (will die loudly if one doesn't exist. So let's hope it does, eh?)
			return self.nicks.get(name=self.name)

	@property
	def abbreviation(self):
		return self.primary_nick.abbreviation

	@property
	def alternative_nicks(self):
		# A queryset of all nicks except the primary one
		return self.nicks.exclude(name=self.name)

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

	@property
	def asciified_real_name(self):
		real_name = self.real_name
		return real_name and unidecode(real_name)

	@property
	def asciified_public_real_name(self):
		real_name = self.public_real_name
		return real_name and unidecode(real_name)

	def real_name_available_to_show(self):
		return (self.first_name and self.show_first_name) or (self.surname and self.show_surname)

	def can_reveal_full_real_name(self):
		return (self.show_first_name and self.show_surname)

	@property
	def all_names_string(self):
		all_names = [nv.name for nv in NickVariant.objects.filter(nick__releaser=self)]
		return ', '.join(all_names)

	@property
	def asciified_all_names_string(self):
		return unidecode(self.all_names_string)

	@property
	def asciified_location(self):
		return self.location and unidecode(self.location)

	@property
	def all_affiliation_names_string(self):
		all_names = [nv.name for nv in NickVariant.objects.filter(nick__releaser__member_memberships__member=self)]
		return ', '.join(all_names)

	# Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
	# that should prevent its deletion
	def is_referenced(self):
		return (
			self.credits().count()
			or self.member_memberships.count()  # A group with members can't be deleted, although a scener with groups can. Seems to make sense...
			or self.productions().count()
			or self.member_productions().count())

	def can_be_converted_to_group(self):
		return (not self.first_name and not self.surname and not self.location)

	def can_be_converted_to_scener(self):
		# don't allow converting a group to scener if it has members or member productions
		return (not self.members() and not self.member_productions())

	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)

	def search_result_json(self):
		primary_nick = self.primary_nick
		if primary_nick.differentiator:
			differentiator = " (%s)" % primary_nick.differentiator
		else:
			differentiator = ""

		return {
			'type': 'group' if self.is_group else 'scener',
			'url': self.get_absolute_url(),
			'value': self.name_with_affiliations() + differentiator,
		}

	class Meta:
		ordering = ['name']
		permissions = (
			("view_releaser_real_names", "Can view non-public real names"),
		)


class Nick(models.Model):
	releaser = models.ForeignKey(Releaser, related_name='nicks')
	name = models.CharField(max_length=255)
	abbreviation = models.CharField(max_length=255, blank=True, help_text="(optional - only if there's one that's actively being used. Don't just make one up!)")
	differentiator = models.CharField(max_length=32, blank=True, help_text="hint text to distinguish from other groups/sceners with the same name - e.g. platform or country")

	def __init__(self, *args, **kwargs):
		super(Nick, self).__init__(*args, **kwargs)
		self._has_written_nick_variant_list = False
		self._nick_variant_list = None

	def __unicode__(self):
		return self.name

	@staticmethod
	def from_id_and_name(id, name):
		if id == 'newgroup':
			releaser = Releaser(name=name, is_group=True, updated_at=datetime.datetime.now())
			releaser.save()
			return releaser.primary_nick
		elif id == 'newscener':
			releaser = Releaser(name=name, is_group=False, updated_at=datetime.datetime.now())
			releaser.save()
			return releaser.primary_nick
		else:
			return Nick.objects.get(id=id)

	def get_nick_variant_list(self):
		if self._has_written_nick_variant_list:
			return self._nick_variant_list
		else:
			variant_names = [variant.name for variant in self.variants.exclude(name__in=[self.name, self.abbreviation])]
			return ", ".join(variant_names)

	def set_nick_variant_list(self, new_list):
		self._nick_variant_list = new_list
		self._has_written_nick_variant_list = True
	nick_variant_list = property(get_nick_variant_list, set_nick_variant_list)

	@property
	def nick_variant_and_abbreviation_list(self):
		variant_names = [variant.name for variant in self.variants.exclude(name=self.name)]
		return ", ".join(variant_names)

	def save(self, *args, **kwargs):
		# update releaser's name if it matches this nick's previous name
		if self.id is not None:
			old_name = Nick.objects.get(id=self.id).name
			super(Nick, self).save(*args, **kwargs)  # Call the original save() method
			if (old_name == self.releaser.name) and (old_name != self.name):
				self.releaser.name = self.name
				self.releaser.save()
		else:
			super(Nick, self).save(*args, **kwargs)  # Call the original save() method
			if not self._has_written_nick_variant_list:
				# force writing a nick variant list containing just the primary nick (and abbreviation if specified)
				self._has_written_nick_variant_list = True
				self._nick_variant_list = ''

		if kwargs.get('commit', True) and self._has_written_nick_variant_list:
			# update the nick variant list
			old_variant_names = [variant.name for variant in self.variants.all()]
			new_variant_names = re.split(r"\s*\,\s*", self._nick_variant_list)
			new_variant_names.append(self.name)
			if self.abbreviation and self.abbreviation.lower() != self.name.lower():
				new_variant_names.append(self.abbreviation)

			for variant in self.variants.all():
				if variant.name not in new_variant_names:
					variant.delete()
			for variant_name in new_variant_names:
				if variant_name and variant_name not in old_variant_names:
					variant = NickVariant(nick=self, name=variant_name)
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

	# Determine whether or not this nick is referenced in any external records (credits, authorships etc)
	def is_referenced(self):
		return (
			self.credits.count()
			or self.productions.count()
			or self.member_productions.count())

	# Reassign credits/productions that reference this nick to use the releaser's primary nick instead,
	# then delete this nick
	def reassign_references_and_delete(self):
		primary_nick = self.releaser.primary_nick
		if primary_nick == self:
			raise Exception("attempted to delete a releaser's primary nick through reassign_references_and_delete!")

		from django.db import connection, transaction
		cursor = connection.cursor()
		cursor.execute("UPDATE demoscene_credit SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
		cursor.execute("UPDATE demoscene_production_author_nicks SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
		cursor.execute("UPDATE demoscene_production_author_affiliation_nicks SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
		transaction.commit_unless_managed()

		self.delete()

	def is_primary_nick(self):
		return (self.releaser.name == self.name)

	class Meta:
		unique_together = ("releaser", "name")
		ordering = ['name']


class NickVariant(models.Model):
	nick = models.ForeignKey(Nick, related_name='variants')
	name = models.CharField(max_length=255)

	def __unicode__(self):
		return self.name

	@staticmethod
	def autocomplete(initial_query, significant_whitespace=True, **kwargs):
		# look for possible autocompletions; choose the top-ranked one and use that as the query
		if significant_whitespace:
			# treat trailing whitespace as a required part of the name
			# (e.g. "Andromeda " will only match "Andromeda Software Development", not "Andromeda"
			autocompletions = NickVariant.autocompletion_search(initial_query, limit=1, **kwargs)
			try:
				result = autocompletions[0].name
				# return just the suffix to add; the caller will append this to the original query,
				# thus preserving capitalisation in exactly the way that iTunes doesn't.
				# (Ha, I rule.)
				return result[len(initial_query):]
			except IndexError:  # no autocompletions available
				return ''
		else:
			# match names which are an EXACT match for the stripped name, or a prefix of the non-stripped
			# name. e.g.: "Andromeda " will match both "Andromeda Software Development" and "Andromeda",
			# but "Far " will only match "Far", not "Farbrausch"

			# look for exact matches first
			autocompletions = NickVariant.autocompletion_search(initial_query.strip(), exact=True, limit=1, **kwargs)
			try:
				result = autocompletions[0].name
				return result[len(initial_query):]
			except IndexError:
				# look for prefixes instead
				autocompletions = NickVariant.autocompletion_search(initial_query, limit=1, **kwargs)
				try:
					result = autocompletions[0].name
					return result[len(initial_query):]
				except IndexError:  # no autocompletions available
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
				nick_variants = NickVariant.objects.filter(name__iexact=query)
			else:
				nick_variants = NickVariant.objects.filter(name__istartswith=query)

			if groups_only:
				nick_variants = nick_variants.filter(nick__releaser__is_group=True)
			elif sceners_only:
				nick_variants = nick_variants.filter(nick__releaser__is_group=False)
			else:
				# nasty hack to ensure that we're joining on releaser, for the 'groups' subquery
				nick_variants = nick_variants.filter(nick__releaser__is_group__in=[True, False])

			if groups:
				nick_variants = nick_variants.extra(
					select=SortedDict([
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
					select_params=(tuple(groups), query),
					order_by=('-score', '-is_exact_match', '-is_primary_nickvariant', 'name')
				)
			elif members:
				nick_variants = nick_variants.extra(
					select=SortedDict([
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
					select_params=(tuple(members), query),
					order_by=('-score', '-is_exact_match', '-is_primary_nickvariant', 'name')
				)
			else:
				nick_variants = nick_variants.extra(
					select=SortedDict([
						('score', '0'),
						('is_exact_match', '''
							CASE WHEN LOWER(demoscene_nickvariant.name) = LOWER(%s) THEN 1 ELSE 0 END
						'''),
						('is_primary_nickvariant', '''
							CASE WHEN demoscene_nick.name = demoscene_nickvariant.name THEN 1 ELSE 0 END
						'''),
					]),
					select_params=(query,),
					order_by=('-is_exact_match', '-is_primary_nickvariant', 'name')
				)
			if limit:
				nick_variants = nick_variants[:limit]

			nick_variants = nick_variants.select_related('nick', 'nick__releaser')
		else:
			nick_variants = NickVariant.objects.none()

		return nick_variants

	class Meta:
		ordering = ['name']


class Membership(models.Model):
	member = models.ForeignKey(Releaser, related_name='group_memberships')
	group = models.ForeignKey(Releaser, limit_choices_to={'is_group': True}, related_name='member_memberships')
	is_current = models.BooleanField(default=True)
	data_source = models.CharField(max_length=32, blank=True, null=True)

	def __unicode__(self):
		return "%s / %s" % (self.member.name, self.group.name)

SUPERTYPE_CHOICES = (
	('production', _('Production')),
	('graphics', _('Graphics')),
	('music', _('Music')),
)


class Production(ModelWithPrefetchSnooping, models.Model):
	title = models.CharField(max_length=255)
	platforms = models.ManyToManyField('Platform', related_name='productions', blank=True)
	supertype = models.CharField(max_length=32, choices=SUPERTYPE_CHOICES)
	types = models.ManyToManyField('ProductionType', related_name='productions')
	author_nicks = models.ManyToManyField('Nick', related_name='productions', blank=True)
	author_affiliation_nicks = models.ManyToManyField('Nick', related_name='member_productions', blank=True, null=True)
	notes = models.TextField(blank=True)
	release_date_date = models.DateField(null=True, blank=True)
	release_date_precision = models.CharField(max_length=1, blank=True, choices=DATE_PRECISION_CHOICES)

	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')
	scene_org_id = models.IntegerField(null=True, blank=True, verbose_name='scene.org ID')

	data_source = models.CharField(max_length=32, blank=True, null=True)
	unparsed_byline = models.CharField(max_length=255, blank=True, null=True)
	has_bonafide_edits = models.BooleanField(default=True, help_text="True if this production has been updated through its own forms, as opposed to just compo results tables")
	default_screenshot = models.ForeignKey('Screenshot', null=True, blank=True, related_name='+', editable=False,
		on_delete=models.SET_NULL,  # don't want deletion to cascade to the production if screenshot is deleted
		help_text="Screenshot to use alongside this production in listings - randomly assigned by script")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField()

	tags = TaggableManager(blank=True)

	search_result_template = 'search/results/production.html'

	# do the equivalent of self.author_nicks.select_related('releaser'), unless that would be
	# less efficient because we've already got the author_nicks relation cached from a prefetch_related
	def author_nicks_with_authors(self):
		if self.has_prefetched('author_nicks'):
			return self.author_nicks.all()
		else:
			return self.author_nicks.select_related('releaser')

	def author_affiliation_nicks_with_groups(self):
		if self.has_prefetched('author_affiliation_nicks'):
			return self.author_affiliation_nicks.all()
		else:
			return self.author_affiliation_nicks.select_related('releaser')

	def save(self, *args, **kwargs):
		if self.id and not self.supertype:
			self.supertype = self.inferred_supertype
		if self.title:
			self.title = self.title.strip()
		return super(Production, self).save(*args, **kwargs)

	def __unicode__(self):
		return self.title

	def byline(self):
		return Byline(self.author_nicks.all(), self.author_affiliation_nicks.all())

	def byline_search(self):
		from demoscene.utils.nick_search import BylineSearch
		if self.unparsed_byline:
			return BylineSearch(self.unparsed_byline)
		else:
			return BylineSearch.from_byline(self.byline())

	def _get_byline_string(self):
		return self.unparsed_byline or unicode(self.byline())

	def _set_byline_string(self, byline_string):
		from demoscene.utils.nick_search import BylineSearch
		byline_search = BylineSearch(byline_string)

		if all(byline_search.author_nick_selections) and all(byline_search.affiliation_nick_selections):
			self.author_nicks = [selection.id for selection in byline_search.author_nick_selections]
			self.author_affiliation_nicks = [selection.id for selection in byline_search.affiliation_nick_selections]
			self.unparsed_byline = None
			self.save()
		else:
			self.unparsed_byline = byline_string
			self.author_nicks = []
			self.author_affiliation_nicks = []
			self.save()
	byline_string = property(_get_byline_string, _set_byline_string)

	@property
	def title_with_byline(self):
		byline = self.byline_string
		if byline:
			return "%s - %s" % (self.title, byline)
		else:
			return self.title

	@property
	def inferred_supertype(self):
		try:
			prod_type = self.types.all()[0]
		except IndexError:
			return 'production'

		return prod_type.supertype

	# given a list of platforms or prod types, return blank if none, name if exactly one, or '(multiple)' otherwise
	@staticmethod
	def list_to_name(platforms):
		if len(platforms) == 0:
			return ''
		elif len(platforms) == 1:
			return platforms[0].name
		else:
			return '(multiple)'

	@property
	def platform_name(self):
		return Production.list_to_name(self.platforms.all())

	@property
	def type_name(self):
		return Production.list_to_name(self.types.all())

	@property
	def asciified_title(self):
		return unidecode(self.title)

	@models.permalink
	def get_absolute_url(self):
		if self.supertype == 'music':
			return ('demoscene.views.music.show', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('demoscene.views.graphics.show', [str(self.id)])
		else:
			return ('demoscene.views.productions.show', [str(self.id)])

	def get_absolute_edit_url(self):
		return self.get_absolute_url()

	@models.permalink
	def get_edit_core_details_url(self):
		if self.supertype == 'music':
			return ('music_edit_core_details', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('graphics_edit_core_details', [str(self.id)])
		else:
			return ('production_edit_core_details', [str(self.id)])

	@models.permalink
	def get_history_url(self):
		if self.supertype == 'music':
			return ('demoscene.views.music.history', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('demoscene.views.graphics.history', [str(self.id)])
		else:
			return ('demoscene.views.productions.history', [str(self.id)])

	def can_have_screenshots(self):
		return (self.supertype != 'music')

	def can_have_soundtracks(self):
		return (self.supertype == 'production')

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
	release_date = property(_get_release_date, _set_release_date)

	# whether this production is regarded as 'stable' in competition results editing;
	# i.e. it will not be deleted or have its details edited in response to actions
	# in the compo results editing interface
	def is_stable_for_competitions(self):
		return self.has_bonafide_edits or self.competition_placings.count() > 1

	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)

	@property
	def tags_string(self):
		return ', '.join([tag.name for tag in self.tags.all()])

	def search_result_json(self):
		if self.default_screenshot:
			width, height = self.default_screenshot.thumb_dimensions_to_fit(48, 36)
			thumbnail = {
				'url': self.default_screenshot.thumbnail_url,
				'width': width, 'height': height,
				'natural_width': self.default_screenshot.thumbnail_width,
				'natural_height': self.default_screenshot.thumbnail_height,
			}
		else:
			thumbnail = None

		return {
			'type': self.supertype,
			'url': self.get_absolute_url(),
			'value': self.title_with_byline,
			'thumbnail': thumbnail
		}

	def credits_for_listing(self):
		return self.credits.select_related('nick__releaser').order_by('nick__name', 'category')

	def get_comments(self):
		return self.comments.select_related('user').order_by('created_at')

	@property
	def platforms_and_types_list(self):
		if self.has_prefetched('platforms'):
			platforms = ', '.join([platform.name for platform in sorted(self.platforms.all(), lambda p:p.name)])
		else:
			platforms = ', '.join([platform.name for platform in self.platforms.order_by('name')])

		if self.has_prefetched('types'):
			prod_types = ', '.join([typ.name for typ in sorted(self.types.all(), lambda t:t.name)])
		else:
			prod_types = ', '.join([typ.name for typ in self.types.order_by('name')])
		if platforms and prod_types:
			return "%s - %s" % (platforms, prod_types)
		else:
			return platforms or prod_types

	def author_twitter_handle(self):
		"""Return the Twitter account name (without the @) of the author of this
		production, or failing that, the Twitter account of the group. Return None
		if there are multiples."""
		try:
			return ReleaserExternalLink.objects.get(releaser__nicks__productions=self, link_class='TwitterAccount').parameter
		except (ReleaserExternalLink.MultipleObjectsReturned, ReleaserExternalLink.DoesNotExist):
			try:
				return ReleaserExternalLink.objects.get(releaser__nicks__member_productions=self, link_class='TwitterAccount').parameter
			except (ReleaserExternalLink.MultipleObjectsReturned, ReleaserExternalLink.DoesNotExist):
				return None

	class Meta:
		ordering = ['title']


# encapsulates list of authors and affiliations
class Byline(StrAndUnicode):
	def __init__(self, authors=[], affiliations=[]):
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
		from demoscene.utils.nick_search import NickSelection

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
				return Byline([Releaser.objects.get(id=releaser_id).primary_nick])
			except Releaser.DoesNotExist:
				pass
		return Byline()


class ProductionDemozoo0Platform(models.Model):
	production = models.ForeignKey(Production, related_name='demozoo0_platforms')
	platform = models.CharField(max_length=64)


class ProductionBlurb(models.Model):
	production = models.ForeignKey(Production, related_name='blurbs')
	body = models.TextField(help_text="A tweet-sized description of this demo, to promote it on listing pages")


class Credit(models.Model):
	CATEGORIES = [
		('Code', 'Code'),
		('Graphics', 'Graphics'),
		('Music', 'Music'),
		('Other', 'Other')
	]

	production = models.ForeignKey(Production, related_name='credits')
	nick = models.ForeignKey(Nick, related_name='credits')
	category = models.CharField(max_length=20, choices=CATEGORIES, blank=True)
	role = models.CharField(max_length=255, blank=True)

	@property
	def description(self):
		if self.role:
			return "%s (%s)" % (self.category, self.role)
		else:
			return self.category

	def __unicode__(self):
		if self.role:
			return "%s: %s - %s (%s)" % (
				self.production_id and self.production.title,
				self.nick_id and self.nick.name,
				self.category,
				self.role)
		else:
			return "%s: %s - %s" % (
				self.production_id and self.production.title,
				self.nick_id and self.nick.name,
				self.category)

	class Meta:
		ordering = ['production__title']


class Screenshot(models.Model):
	production = models.ForeignKey(Production, related_name='screenshots')
	original_url = models.CharField(max_length=255, blank=True)
	original_width = models.IntegerField(editable=False, null=True, blank=True)
	original_height = models.IntegerField(editable=False, null=True, blank=True)

	thumbnail_url = models.CharField(max_length=255, blank=True)
	thumbnail_width = models.IntegerField(editable=False, null=True, blank=True)
	thumbnail_height = models.IntegerField(editable=False, null=True, blank=True)

	standard_url = models.CharField(max_length=255, blank=True)
	standard_width = models.IntegerField(editable=False, null=True, blank=True)
	standard_height = models.IntegerField(editable=False, null=True, blank=True)

	# for diagnostics: ID of the mirror.models.Download instance that this screen was generated from
	source_download_id = models.IntegerField(editable=False, null=True, blank=True)

	def thumb_dimensions_to_fit(self, width, height):
		# return the width and height to render the thumbnail image at in order to fit within the given
		# width/height while preserving aspect ratio

		thumbnail_width = self.thumbnail_width or 1
		thumbnail_height = self.thumbnail_height or 1

		width_scale = min(float(width) / thumbnail_width, 1)
		height_scale = min(float(height) / thumbnail_height, 1)
		scale = min(width_scale, height_scale)

		return (round(thumbnail_width * scale), round(thumbnail_height * scale))


	def __unicode__(self):
		return "%s - %s" % (self.production.title, self.original_url)


class AccountProfile(models.Model):
	user = models.ForeignKey(User, unique=True)
	sticky_edit_mode = models.BooleanField(help_text="Stays in edit mode when browsing around, until you explicitly hit 'done'")
	edit_mode_active = models.BooleanField(editable=False)
	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')

	def __unicode__(self):
		try:
			return self.user.__unicode__()
		except User.DoesNotExist:
			return "(AccountProfile)"

	class Meta:
		ordering = ['user__username']


class SoundtrackLink(models.Model):
	production = models.ForeignKey(Production, related_name='soundtrack_links')
	soundtrack = models.ForeignKey(Production, limit_choices_to={'supertype': 'music'}, related_name='appearances_as_soundtrack')
	position = models.IntegerField()

	def __unicode__(self):
		return "%s on %s" % (self.soundtrack, self.production)

	class Meta:
		ordering = ['position']


class ExternalLink(models.Model):
	link_class = models.CharField(max_length=100)
	parameter = models.CharField(max_length=255)

	def _get_url(self):
		if self.link:
			return unicode(self.link)
		else:
			return None

	def _set_url(self, urlstring):
		if urlstring:
			self.link = groklinks.grok_link_by_types(urlstring, self.link_types)
			if self.link:
				self.link_class = self.link.__class__.__name__
				self.parameter = self.link.param
			else:
				self.link_class = None
				self.parameter = None
		else:
			self.link_class = None
			self.parameter = None
	url = property(_get_url, _set_url)

	def __init__(self, *args, **kwargs):
		super(ExternalLink, self).__init__(*args, **kwargs)
		if self.link_class:
			self.link = groklinks.__dict__[self.link_class](self.parameter)
		else:
			self.link = None

	@property
	def sort_key(self):
		return '0000' if self.link_class == 'BaseUrl' else self.link_class

	class Meta:
		abstract = True
		ordering = ['link_class']


class ReleaserExternalLink(ExternalLink):
	releaser = models.ForeignKey(Releaser, related_name='external_links')
	link_types = groklinks.RELEASER_LINK_TYPES

	def html_link(self):
		return self.link.as_html(self.releaser.name)

	class Meta:
		unique_together = (
			('link_class', 'parameter', 'releaser'),
		)
		ordering = ['link_class']


class ProductionLink(ExternalLink):
	production = models.ForeignKey(Production, related_name='links')
	is_download_link = models.BooleanField()
	description = models.CharField(max_length=255, blank=True)
	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')
	file_for_screenshot = models.CharField(max_length=255, blank=True, help_text='The file within this archive which has been identified as most suitable for generating a screenshot from')
	is_unresolved_for_screenshotting = models.BooleanField(default=False, help_text="Indicates that we've tried and failed to identify the most suitable file in this archive to generate a screenshot from")

	link_types = groklinks.PRODUCTION_LINK_TYPES

	def save(self, *args, **kwargs):
		# certain link types are marked as always download links, or always external links,
		# regardless of where they are entered -
		# if this is one of those types, ensure that is_download_link is set appropriately
		if self.link_class in groklinks.PRODUCTION_DOWNLOAD_LINK_TYPES:
			self.is_download_link = True
		elif self.link_class in groklinks.PRODUCTION_EXTERNAL_LINK_TYPES:
			self.is_download_link = False

		super(ProductionLink, self).save(*args, **kwargs)

	def html_link(self):
		return self.link.as_html(self.production.title)

	def html_link_class(self):
		return self.link.html_link_class

	def as_download_link(self):
		return self.link.as_download_link()

	@property
	def download_url(self):
		return self.link.download_url

	def download_file_extension(self):
		filename = self.download_url.split('/')[-1]
		extension = filename.split('.')[-1]
		if filename == extension:
			# filename has no extension
			return None
		else:
			return extension.lower()

	def is_zip_file(self):
		return self.download_file_extension() == 'zip'

	class Meta:
		unique_together = (
			('link_class', 'parameter', 'production', 'is_download_link'),
		)
		ordering = ['link_class']


class Edit(models.Model):
	action_type = models.CharField(max_length=100)

	focus_content_type = models.ForeignKey(ContentType, related_name='edits')
	focus_object_id = models.PositiveIntegerField()
	focus = generic.GenericForeignKey('focus_content_type', 'focus_object_id')

	focus2_content_type = models.ForeignKey(ContentType, null=True, blank=True, related_name='edits_as_focus2')
	focus2_object_id = models.PositiveIntegerField(null=True, blank=True)
	focus2 = generic.GenericForeignKey('focus2_content_type', 'focus2_object_id')

	description = models.TextField()
	user = models.ForeignKey(User)
	timestamp = models.DateTimeField(auto_now_add=True)

	admin_only = models.BooleanField(default=False)

	@staticmethod
	def for_model(model, is_admin=False):
		model_type = ContentType.objects.get_for_model(model)
		edits = Edit.objects.all()
		if not is_admin:
			edits = edits.filter(admin_only=False)
		edits = edits.extra(where=["""(
			(focus_content_type_id = %s AND focus_object_id = %s)
			OR (focus2_content_type_id = %s AND focus2_object_id = %s)
		)"""], params=[model_type.id, model.id, model_type.id, model.id]).order_by('-timestamp').select_related('user')
		return edits

class CaptchaQuestion(models.Model):
	question = models.TextField(help_text="HTML is allowed. Keep questions factual and simple - remember that our potential users are not always followers of mainstream demoparty culture")
	answer = models.CharField(max_length=255, help_text="Answers are not case sensitive (the correct answer will be accepted regardless of capitalisation)")

	def __unicode__(self):
		return self.question
