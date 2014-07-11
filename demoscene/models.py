from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.datastructures import SortedDict
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

import re
import datetime

from unidecode import unidecode

from strip_markup import strip_markup
from prefetch_snooping import ModelWithPrefetchSnooping
from demoscene.utils import groklinks

DATE_PRECISION_CHOICES = [
	('d', 'Day'),
	('m', 'Month'),
	('y', 'Year'),
]


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
		from productions.models import Production
		return Production.objects.filter(author_nicks__releaser=self)

	def member_productions(self):
		# Member productions are those which list this group in the 'affiliations' portion of the byline,
		# OR the author is a SUBGROUP of this group (regardless of whether this parent group is named as an affiliation).
		from productions.models import Production

		subgroup_ids = self.member_memberships.filter(member__is_group=True).values_list('member_id', flat=True)

		return Production.objects.filter(
			Q(author_affiliation_nicks__releaser=self)
			| Q(author_nicks__releaser__in=subgroup_ids)
		).distinct()

	def credits(self):
		from productions.models import Credit
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
		cursor.execute("UPDATE productions_credit SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
		cursor.execute("UPDATE productions_production_author_nicks SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
		cursor.execute("UPDATE productions_production_author_affiliation_nicks SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
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


class AccountProfile(models.Model):
	user = models.ForeignKey(User, unique=True)
	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')

	def __unicode__(self):
		try:
			return self.user.__unicode__()
		except User.DoesNotExist:
			return "(AccountProfile)"

	class Meta:
		ordering = ['user__username']


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


class TagDescription(models.Model):
	tag = models.OneToOneField('taggit.Tag', primary_key=True, related_name='description')
	description = models.TextField(help_text="HTML is allowed. Keep this to a couple of sentences at most - it's used in tooltips as well as the tag listing page")

	def __unicode__(self):
		return self.tag.name
