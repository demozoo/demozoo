import datetime
import hashlib
import re

from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from fuzzy_date import FuzzyDate
from strip_markup import strip_markup
from unidecode import unidecode

from demoscene.models import DATE_PRECISION_CHOICES, ExternalLink
from demoscene.utils import groklinks
from comments.models import Commentable
from productions.models import Production, Screenshot


class PartySeries(models.Model):
	name = models.CharField(max_length=255, unique=True)
	notes = models.TextField(blank=True)
	website = models.URLField(blank=True)
	twitter_username = models.CharField(max_length=30, blank=True)
	pouet_party_id = models.IntegerField(null=True, blank=True, verbose_name='Pouet party ID')

	def __unicode__(self):
		return self.name

	@models.permalink
	def get_absolute_url(self):
		return ('parties.views.parties.show_series', [str(self.id)])

	@models.permalink
	def get_absolute_edit_url(self):
		return ('parties.views.parties.show_series', [str(self.id)])

	@models.permalink
	def get_history_url(self):
		return ('parties.views.parties.series_history', [str(self.id)])

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
		ordering = ("name",)


class PartySeriesDemozoo0Reference(models.Model):
	party_series = models.ForeignKey(PartySeries, related_name='demozoo0_ids')
	demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name='Demozoo v0 ID')


class Party(Commentable):
	party_series = models.ForeignKey(PartySeries, related_name='parties')
	name = models.CharField(max_length=255, unique=True)
	tagline = models.CharField(max_length=255, blank=True)
	start_date_date = models.DateField()
	start_date_precision = models.CharField(max_length=1, choices=DATE_PRECISION_CHOICES)
	end_date_date = models.DateField()
	end_date_precision = models.CharField(max_length=1, choices=DATE_PRECISION_CHOICES)

	is_online = models.BooleanField(default=False)
	location = models.CharField(max_length=255, blank=True)
	country_code = models.CharField(max_length=5, blank=True)
	latitude = models.FloatField(null=True, blank=True)
	longitude = models.FloatField(null=True, blank=True)
	woe_id = models.BigIntegerField(null=True, blank=True)
	geonames_id = models.BigIntegerField(null=True, blank=True)

	notes = models.TextField(blank=True)
	website = models.URLField(blank=True)

	sceneorg_compofolders_done = models.BooleanField(default=False, help_text="Indicates that all compos at this party have been matched up with the corresponding scene.org directory")

	invitations = models.ManyToManyField('productions.Production', related_name='invitation_parties', blank=True)
	releases = models.ManyToManyField('productions.Production', related_name='release_parties', blank=True)

	search_result_template = 'search/results/party.html'

	def __unicode__(self):
		return self.name

	@models.permalink
	def get_absolute_url(self):
		return ('parties.views.parties.show', [str(self.id)])

	@models.permalink
	def get_absolute_edit_url(self):
		return ('parties.views.parties.show', [str(self.id)])

	@models.permalink
	def get_history_url(self):
		return ('parties.views.parties.history', [str(self.id)])

	@property
	def suffix(self):
		series_name = self.party_series.name
		if series_name == self.name and self.start_date:
			return self.start_date.date.year
		else:
			return re.sub(r"^" + re.escape(series_name) + r"\s+", '', self.name)

	@property
	def asciified_name(self):
		return unidecode(self.name)

	@property
	def asciified_location(self):
		return self.location and unidecode(self.location)

	def _get_start_date(self):
		return FuzzyDate(self.start_date_date, self.start_date_precision)

	def _set_start_date(self, fuzzy_date):
		self.start_date_date = fuzzy_date.date
		self.start_date_precision = fuzzy_date.precision
	start_date = property(_get_start_date, _set_start_date)

	def _get_end_date(self):
		return FuzzyDate(self.end_date_date, self.end_date_precision)

	def _set_end_date(self, fuzzy_date):
		self.end_date_date = fuzzy_date.date
		self.end_date_precision = fuzzy_date.precision
	end_date = property(_get_end_date, _set_end_date)

	def random_screenshot(self):
		screenshots = Screenshot.objects.filter(production__competition_placings__competition__party=self)
		try:
			return screenshots.order_by('?')[0]
		except IndexError:
			return None

	# return a FuzzyDate representing our best guess at when this party's competitions were held
	def default_competition_date(self):
		if self.end_date and self.end_date.precision == 'd':
			# assume that competitions were held on the penultimate day of the party
			competition_day = self.end_date.date - datetime.timedelta(days=1)
			# ...but if that's in the future, use today instead
			if competition_day > datetime.date.today():
				competition_day = datetime.date.today()
			# ...and if that's before the (known exact) start date of the party, use that instead
			if self.start_date and self.start_date.precision == 'd' and self.start_date.date > competition_day:
				competition_day = self.start_date.date
			return FuzzyDate(competition_day, 'd')
		else:
			# we don't know this party's exact end date, so just use whatever precision of end date
			# we know (if indeed we have one at all)
			return self.end_date

	@property
	def plaintext_notes(self):
		return strip_markup(self.notes)

	# return the sceneorg.models.File instance for our best guess at the results textfile in this
	# party's folder on scene.org
	def sceneorg_results_file(self):
		from sceneorg.models import File as SceneOrgFile
		sceneorg_dirs = self.external_links.filter(link_class='SceneOrgFolder')
		for sceneorg_dir in sceneorg_dirs:
			for subpath in ['info/results.txt', 'misc/results.txt', 'results.txt']:
				try:
					return SceneOrgFile.objects.get(path=sceneorg_dir.parameter + subpath, is_deleted=False)
				except SceneOrgFile.DoesNotExist:
					pass

	# add the passed sceneorg.models.File instance as a ResultsFile for this party
	# NB best to do this through a celery task, as it requires an FTP fetch from scene.org
	def add_sceneorg_file_as_results_file(self, sceneorg_file):
		results_file = ResultsFile(
			party=self,
			filename=sceneorg_file.filename(),
		)
		results_file.file.save(self.clean_name + '.txt', ContentFile(sceneorg_file.fetched_data()))
		# this also commits the ResultsFile record to the database

	def search_result_json(self):
		return {
			'type': 'party',
			'url': self.get_absolute_url(),
			'value': self.name,
		}

	@property
	def clean_name(self):
		"""a name for this party that can be used in filenames (used to give results.txt files
			meaningful names on disk)"""
		return re.sub(r'\W+', '_', self.name.lower())

	class Meta:
		verbose_name_plural = "Parties"
		ordering = ("name",)


class PartyExternalLink(ExternalLink):
	party = models.ForeignKey(Party, related_name='external_links')
	link_types = groklinks.PARTY_LINK_TYPES

	def html_link(self):
		return self.link.as_html(self.party.name)

	class Meta:
		unique_together = (
			('link_class', 'parameter', 'party'),
		)
		ordering = ['link_class']


class Competition(models.Model):
	party = models.ForeignKey(Party, related_name='competitions')
	name = models.CharField(max_length=255)
	shown_date_date = models.DateField(null=True, blank=True)
	shown_date_precision = models.CharField(max_length=1, blank=True, choices=DATE_PRECISION_CHOICES)
	platform = models.ForeignKey('platforms.Platform', blank=True, null=True)
	production_type = models.ForeignKey('productions.ProductionType', blank=True, null=True)

	def results(self):
		return self.placings.order_by('position')

	def __unicode__(self):
		try:
			return "%s %s" % (self.party.name, self.name)
		except Party.DoesNotExist:
			return "(unknown party) %s" % self.name

	def _get_shown_date(self):
		if self.shown_date_date and self.shown_date_precision:
			return FuzzyDate(self.shown_date_date, self.shown_date_precision)
		else:
			return None

	def _set_shown_date(self, fuzzy_date):
		if fuzzy_date:
			self.shown_date_date = fuzzy_date.date
			self.shown_date_precision = fuzzy_date.precision
		else:
			self.shown_date_date = None
			self.shown_date_precision = ''
	shown_date = property(_get_shown_date, _set_shown_date)

	@models.permalink
	def get_absolute_url(self):
		return ('parties.views.competitions.show', [str(self.id)])

	@models.permalink
	def get_history_url(self):
		return ('parties.views.competitions.history', [str(self.id)])

	class Meta:
		ordering = ("party__name", "name")


class CompetitionPlacing(models.Model):
	competition = models.ForeignKey(Competition, related_name='placings')
	production = models.ForeignKey('productions.Production', related_name='competition_placings')
	ranking = models.CharField(max_length=32, blank=True)
	position = models.IntegerField()
	score = models.CharField(max_length=32, blank=True)

	@property
	def json_data(self):
		if self.production.is_stable_for_competitions():
			return {
				'id': self.id,
				'ranking': self.ranking,
				'score': self.score,
				'production': {
					'id': self.production.id,
					'title': self.production.title,
					'byline': self.production.byline_string,
					'url': self.production.get_absolute_url(),
					'platform_name': self.production.platform_name,
					'production_type_name': self.production.type_name,
					'stable': True,
				}
			}
		else:
			byline_search = self.production.byline_search()
			return {
				'id': self.id,
				'ranking': self.ranking,
				'score': self.score,
				'production': {
					'id': self.production.id,
					'title': self.production.title,
					'platform': self.production.platforms.all()[0].id if self.production.platforms.all() else None,
					'production_type': self.production.types.all()[0].id if self.production.types.all() else None,
					# it's OK to reduce platform / prodtype to a single value, because unstable productions
					# can only ever have one (adding multiple on the production edit page would make them stable)
					'byline': {
						'search_term': byline_search.search_term,
						'author_matches': byline_search.author_matches_data,
						'affiliation_matches': byline_search.affiliation_matches_data,
					},
					'stable': False,
				}
			}

	def __unicode__(self):
		try:
			return self.production.__unicode__()
		except Production.DoesNotExist:
			return "(CompetitionPlacing)"


class ResultsFile(models.Model):
	party = models.ForeignKey(Party, related_name='results_files')
	filename = models.CharField(max_length=255, blank=True)
	file = models.FileField(storage=FileSystemStorage(), upload_to='results', blank=True)
	filesize = models.IntegerField()
	sha1 = models.CharField(max_length=40)
	encoding = models.CharField(blank=True, null=True, max_length=32)

	def save(self, *args, **kwargs):
		data = self.data
		self.filesize = len(data)
		self.sha1 = hashlib.sha1(data).hexdigest()
		if not self.encoding:
			decode = self.guess_encoding(data)
			if decode:
				self.encoding = decode[0]
		super(ResultsFile, self).save(*args, **kwargs)

	@staticmethod
	def guess_encoding(data, fuzzy=False):
		"""
		Make a best guess at what character encoding this data is in.
		Returns a tuple of (encoding, decoded_data).
		If fuzzy=False, we return None if the encoding is uncertain;
		if fuzzy=True, we make a wild guess.
		"""
		# Try to decode the data using several candidate encodings, least permissive first.
		# Accept the first one that doesn't break.
		if fuzzy:
			candidate_encodings = ['ascii', 'utf-8', 'windows-1252', 'iso-8859-1']
		else:
			candidate_encodings = ['ascii', 'utf-8']

		for encoding in candidate_encodings:
			try:
				return (encoding, data.decode(encoding))
			except UnicodeDecodeError:
				pass

	@property
	def data(self):
		self.file.open()
		data = self.file.read()
		self.file.close()
		return data

	@property
	def text(self):
		if self.encoding:
			return self.data.decode(self.encoding)
		else:
			encoding, output = self.guess_encoding(self.data, fuzzy=True)
			return output
