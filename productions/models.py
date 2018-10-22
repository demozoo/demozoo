from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
# from django.utils.encoding import StrAndUnicode
from django.utils.translation import ugettext_lazy as _

from collections import defaultdict
import datetime
import random

from taggit.managers import TaggableManager
from treebeard.mp_tree import MP_Node
from unidecode import unidecode
from lib.fuzzy_date import FuzzyDate
from lib.prefetch_snooping import ModelWithPrefetchSnooping
from lib.strip_markup import strip_markup

from comments.models import Commentable
from demoscene.models import DATE_PRECISION_CHOICES, Releaser, Nick, ReleaserExternalLink, ExternalLink, TextFile
from demoscene.utils import groklinks
from demoscene.utils.text import generate_search_title, generate_sort_key
from mirror.models import Download, ArchiveMember


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
	supertype = models.CharField(max_length=32, choices=SUPERTYPE_CHOICES, db_index=True)
	types = models.ManyToManyField('ProductionType', related_name='productions')
	author_nicks = models.ManyToManyField('demoscene.Nick', related_name='productions', blank=True)
	author_affiliation_nicks = models.ManyToManyField('demoscene.Nick', related_name='member_productions', blank=True)
	notes = models.TextField(blank=True)
	release_date_date = models.DateField(null=True, blank=True)
	release_date_precision = models.CharField(max_length=1, blank=True, choices=DATE_PRECISION_CHOICES)

	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')
	scene_org_id = models.IntegerField(null=True, blank=True, verbose_name='scene.org ID')

	data_source = models.CharField(max_length=32, blank=True, null=True)
	unparsed_byline = models.CharField(max_length=255, blank=True, null=True)
	has_bonafide_edits = models.BooleanField(default=True, help_text="True if this production has been updated through its own forms, as opposed to just compo results tables")
	has_screenshot = models.BooleanField(default=False, editable=False, help_text="True if this prod has at least one (processed) screenshot")
	include_notes_in_search = models.BooleanField(default=True,
		help_text="Whether the notes field for this production will be indexed. (Untick this to avoid false matches in search results e.g. 'this demo was not by Magic / Nah-Kolor')")

	sortable_title = models.CharField(max_length=255, blank=True, null=True, db_index=True)
	search_title = models.CharField(max_length=255, blank=True, null=True, db_index=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField()

	tags = TaggableManager(blank=True)

	search_document = SearchVectorField(null=True, editable=False)

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

		# populate search_title and sortable_title from title
		if self.title:
			self.title = self.title.strip()
			self.search_title = generate_search_title(self.title)
			self.sortable_title = generate_sort_key(self.title)

		# auto-populate updated_at; this will only happen on creation
		# because it's a non-null field at the db level
		if self.updated_at is None:
			self.updated_at = datetime.datetime.now()

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

	@models.permalink
	def get_all_screenshots_url(self):
		return ('production_artwork' if self.supertype == 'music' else 'production_screenshots', [str(self.id)])

	@models.permalink
	def get_add_screenshot_url(self):
		return ('production_add_artwork' if self.supertype == 'music' else 'production_add_screenshot', [str(self.id)])

	@models.permalink
	def get_edit_screenshots_url(self):
		return ('production_edit_artwork' if self.supertype == 'music' else 'production_edit_screenshots', [str(self.id)])

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

	def credits_for_listing(self):
		return self.credits.select_related('nick__releaser').extra(
			select={'category_order': "CASE WHEN category = 'Other' THEN 'zzzother' ELSE category END"}
		).order_by('nick__name', 'category_order')

	@property
	def platforms_and_types_list(self):
		if self.has_prefetched('platforms'):
			platforms = ', '.join(sorted([platform.name for platform in self.platforms.all()]))
		else:
			platforms = ', '.join([platform.name for platform in self.platforms.order_by('name')])

		if self.has_prefetched('types'):
			prod_types = ', '.join(sorted([typ.name for typ in self.types.all()]))
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

	@property
	def external_links(self):
		external_links = self.links.filter(is_download_link=False).exclude(link_class__in=groklinks.ARCHIVED_LINK_TYPES)
		return sorted(external_links, key=lambda obj: obj.sort_key)

	@property
	def download_links(self):
		return self.links.filter(is_download_link=True).exclude(link_class__in=groklinks.ARCHIVED_LINK_TYPES)

	def index_components(self):
		return {
			'A': self.asciified_title,
			'C': self.tags_string + ' ' + self.indexed_notes
		}

	class Meta:
		ordering = ['sortable_title']
		indexes = [
			GinIndex(fields=['search_document']),
		]
		index_together = [
			['release_date_date', 'created_at']
		]


# encapsulates list of authors and affiliations
class Byline(object):
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
	production = models.ForeignKey(Production, related_name='demozoo0_platforms', on_delete=models.CASCADE)
	platform = models.CharField(max_length=64)


class ProductionBlurb(models.Model):
	production = models.ForeignKey(Production, related_name='blurbs', on_delete=models.CASCADE)
	body = models.TextField(help_text="A tweet-sized description of this demo, to promote it on listing pages")


class Credit(models.Model):
	CATEGORIES = [
		('Code', 'Code'),
		('Graphics', 'Graphics'),
		('Music', 'Music'),
		('Text', 'Text'),
		('Other', 'Other')
	]

	production = models.ForeignKey(Production, related_name='credits', on_delete=models.CASCADE)
	nick = models.ForeignKey(Nick, related_name='credits', on_delete=models.CASCADE)
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
	production = models.ForeignKey(Production, related_name='screenshots', on_delete=models.CASCADE)
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

		# Mark the corresponding production as having a screenshot
		if self.thumbnail_url and not self.production.has_screenshot:
			self.production.has_screenshot = True
			self.production.save(update_fields=['has_screenshot'])

		# if any production links for this production have is_unresolved_for_screenshotting=True,
		# reset that flag since we no longer need a screenshot
		self.production.links.filter(is_unresolved_for_screenshotting=True).update(is_unresolved_for_screenshotting=False)

	def __unicode__(self):
		return "%s - %s" % (self.production.title, self.original_url)

	@staticmethod
	def select_for_production_ids(production_ids):
		"""
		Given a list of production ids, return a dict mapping production id to a random
		screenshot for each production in the list that has screenshots
		"""
		prod_and_screenshot_ids = Screenshot.objects.filter(
			production_id__in=production_ids
		).exclude(
			thumbnail_url=''
		).values_list('production_id', 'id')

		screenshots_by_prod_id = defaultdict(list)
		for (prod_id, screenshot_id) in prod_and_screenshot_ids:
			screenshots_by_prod_id[prod_id].append(screenshot_id)

		chosen_screenshot_ids = [
			random.choice(screenshot_id_set)
			for screenshot_id_set in screenshots_by_prod_id.values()
		]

		return {
			screenshot.production_id: screenshot
			for screenshot in Screenshot.objects.filter(id__in=chosen_screenshot_ids)
		}


@receiver(post_delete, sender=Screenshot)
def update_prod_screenshot_data_on_delete(sender, **kwargs):
	production = kwargs['instance'].production
	# look for remaining screenshots
	screenshots = production.screenshots.exclude(original_url='')

	production.has_screenshot = bool(screenshots)
	production.save(update_fields=['has_screenshot'])


class SoundtrackLink(models.Model):
	production = models.ForeignKey(Production, related_name='soundtrack_links', on_delete=models.CASCADE)
	soundtrack = models.ForeignKey(Production, limit_choices_to={'supertype': 'music'}, related_name='appearances_as_soundtrack', on_delete=models.CASCADE)
	position = models.IntegerField()

	def __unicode__(self):
		return "%s on %s" % (self.soundtrack, self.production)

	class Meta:
		ordering = ['position']


class PackMember(models.Model):
	pack = models.ForeignKey(Production, related_name='pack_members', on_delete=models.CASCADE)
	member = models.ForeignKey(Production, related_name='packed_in', on_delete=models.CASCADE)
	position = models.IntegerField()

	def __unicode__(self):
		return "%s packed in %s" % (self.member, self.pack)

	class Meta:
		ordering = ['position']


class ProductionLink(ExternalLink):
	production = models.ForeignKey(Production, related_name='links', on_delete=models.CASCADE)
	is_download_link = models.BooleanField()
	description = models.CharField(max_length=255, blank=True)
	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')
	file_for_screenshot = models.CharField(max_length=255, blank=True, help_text='The file within this archive which has been identified as most suitable for generating a screenshot from')
	is_unresolved_for_screenshotting = models.BooleanField(default=False, help_text="Indicates that we've tried and failed to identify the most suitable file in this archive to generate a screenshot from")
	has_bad_image = models.BooleanField(default=False, help_text="Indicates that an attempt to create a screenshot from this link has failed at the image processing stage")
	source = models.CharField(max_length=32, blank=True, editable=False, help_text="Identifier to indicate where this link came from - e.g. manual (entered via form), match, auto")

	thumbnail_url = models.CharField(max_length=255, blank=True, editable=False)
	thumbnail_width = models.IntegerField(null=True, blank=True, editable=False)
	thumbnail_height = models.IntegerField(null=True, blank=True, editable=False)
	video_width = models.IntegerField(null=True, blank=True, editable=False)
	video_height = models.IntegerField(null=True, blank=True, editable=False)
	embed_data_last_fetch_time = models.DateTimeField(null=True, blank=True, editable=False)
	embed_data_last_error_time = models.DateTimeField(null=True, blank=True, editable=False)

	link_types = groklinks.PRODUCTION_LINK_TYPES

	def __init__(self, *args, **kwargs):
		super(ProductionLink, self).__init__(*args, **kwargs)
		if self.pk:
			self._original_link_class = self.link_class
			self._original_parameter = self.parameter
		else:
			self._original_link_class = None
			self._original_link_class = None

	def save(self, *args, **kwargs):
		# certain link types are marked as always download links, or always external links,
		# regardless of where they are entered -
		# if this is one of those types, ensure that is_download_link is set appropriately
		if self.link_class in groklinks.PRODUCTION_DOWNLOAD_LINK_TYPES:
			self.is_download_link = True
		elif self.link_class in groklinks.PRODUCTION_EXTERNAL_LINK_TYPES:
			self.is_download_link = False

		should_fetch_embed_data = False

		if self._original_link_class != self.link_class or self._original_parameter != self.parameter:
			# link has changed - remove old embed data
			self.thumbnail_url = ''
			self.thumbnail_width = None
			self.thumbnail_height = None
			self.video_width = None
			self.video_height = None
			self.embed_data_last_fetch_time = None
			self.embed_data_last_error_time = None

			if self.link.supports_embed_data:
				should_fetch_embed_data = True

			self._original_link_class = self.link_class
			self._original_parameter = self.parameter

		super(ProductionLink, self).save(*args, **kwargs)

		if should_fetch_embed_data:
			from productions.tasks import fetch_production_link_embed_data
			fetch_production_link_embed_data.delay(self.pk)

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

	def fetch_embed_data(self):
		embed_data = self.link.get_embed_data()
		if embed_data is not None:
			self.thumbnail_url = embed_data['thumbnail_url']
			self.thumbnail_width = embed_data['thumbnail_width']
			self.thumbnail_height = embed_data['thumbnail_height']
			self.video_width = embed_data['video_width']
			self.video_height = embed_data['video_height']
			self.embed_data_last_fetch_time = datetime.datetime.now()
			self.save()

	def last_successful_download(self):
		return Download.objects.filter(
			link_class=self.link_class, parameter=self.parameter
		).exclude(sha1='').order_by('-downloaded_at').first()

	def archive_members(self):
		download = self.last_successful_download()
		if download:
			return ArchiveMember.objects.filter(archive_sha1=download.sha1)
		else:
			return ArchiveMember.objects.none()

	def is_believed_downloadable(self):
		# mirrored files are always downloadable
		mirrored_downloads = Download.objects.filter(
			link_class=self.link_class, parameter=self.parameter
		).exclude(mirror_s3_key='')
		if mirrored_downloads.exists():
			return True

		last_download = Download.objects.filter(
			link_class=self.link_class, parameter=self.parameter
		).order_by('-downloaded_at').first()
		if last_download is None:
			# no previous downloads, so assume good
			return True

		# if we got a FileTooBig response last time, assume it'll never be downloadable
		if last_download.error_type == 'FileTooBig':
			return False

		# if we got an error last time, and that was less than a month ago, don't retry
		last_month = datetime.datetime.now() - datetime.timedelta(days=30)
		if last_download.error_type != '' and last_download.downloaded_at > last_month:
			return False

		return True

	class Meta:
		unique_together = (
			('link_class', 'parameter', 'production', 'is_download_link'),
		)
		ordering = ['link_class']
		index_together = [
			['link_class', 'parameter']
		]


class Ansi(models.Model):
	production = models.ForeignKey(Production, related_name='ansis', on_delete=models.CASCADE)
	url = models.URLField(max_length=255)


class InfoFile(TextFile):
	production = models.ForeignKey(Production, related_name='info_files', on_delete=models.CASCADE)
	file = models.FileField(upload_to='nfo', blank=True)
