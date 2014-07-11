from django.db import models
from django.utils.encoding import StrAndUnicode
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager
from treebeard.mp_tree import MP_Node
from unidecode import unidecode
from fuzzy_date import FuzzyDate
from prefetch_snooping import ModelWithPrefetchSnooping
from strip_markup import strip_markup

from comments.models import Commentable
from demoscene.models import DATE_PRECISION_CHOICES, Releaser, Nick, ReleaserExternalLink, ExternalLink
from demoscene.utils import groklinks


SUPERTYPE_CHOICES = (
	('production', _('Production')),
	('graphics', _('Graphics')),
	('music', _('Music')),
)

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


class Production(ModelWithPrefetchSnooping, Commentable):
	title = models.CharField(max_length=255)
	platforms = models.ManyToManyField('platforms.Platform', related_name='productions', blank=True)
	supertype = models.CharField(max_length=32, choices=SUPERTYPE_CHOICES)
	types = models.ManyToManyField('ProductionType', related_name='productions')
	author_nicks = models.ManyToManyField('demoscene.Nick', related_name='productions', blank=True)
	author_affiliation_nicks = models.ManyToManyField('demoscene.Nick', related_name='member_productions', blank=True, null=True)
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
	include_notes_in_search = models.BooleanField(default=True,
		help_text="Whether the notes field for this production will be indexed. (Untick this to avoid false matches in search results e.g. 'this demo was not by Magic / Nah-Kolor')")

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
			return ('music', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('graphic', [str(self.id)])
		else:
			return ('production', [str(self.id)])

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
			return ('music_history', [str(self.id)])
		elif self.supertype == 'graphics':
			return ('graphics_history', [str(self.id)])
		else:
			return ('production_history', [str(self.id)])

	def can_have_screenshots(self):
		return (self.supertype != 'music')

	def can_have_soundtracks(self):
		return (self.supertype == 'production')

	def can_have_pack_members(self):
		return any([typ.internal_name == 'pack' for typ in self.types.all()])

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
	def indexed_notes(self):
		return self.plaintext_notes if self.include_notes_in_search else ''

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
		return self.credits.select_related('nick__releaser').extra(
			select={'category_order': "CASE WHEN category = 'Other' THEN 'zzzother' ELSE category END"}
		).order_by('nick__name', 'category_order')

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
		('Text', 'Text'),
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

	def save(self, *args, **kwargs):
		super(Screenshot, self).save(*args, **kwargs)

		# If the production does not already have a default_screenshot, and this screenshot has
		# a thumbnail available, set this as the default
		if self.thumbnail_url and (self.production.default_screenshot_id is None):
			self.production.default_screenshot = self
			self.production.save()

	def __unicode__(self):
		return "%s - %s" % (self.production.title, self.original_url)


class SoundtrackLink(models.Model):
	production = models.ForeignKey(Production, related_name='soundtrack_links')
	soundtrack = models.ForeignKey(Production, limit_choices_to={'supertype': 'music'}, related_name='appearances_as_soundtrack')
	position = models.IntegerField()

	def __unicode__(self):
		return "%s on %s" % (self.soundtrack, self.production)

	class Meta:
		ordering = ['position']


class PackMember(models.Model):
	pack = models.ForeignKey(Production, related_name='pack_members')
	member = models.ForeignKey(Production, related_name='packed_in')
	position = models.IntegerField()

	def __unicode__(self):
		return "%s packed in %s" % (self.member, self.pack)

	class Meta:
		ordering = ['position']


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

	@property
	def is_streaming_video(self):
		return getattr(self.link, 'is_streaming_video', False)

	class Meta:
		unique_together = (
			('link_class', 'parameter', 'production', 'is_download_link'),
		)
		ordering = ['link_class']
