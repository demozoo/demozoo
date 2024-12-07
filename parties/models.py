import datetime
import re

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from unidecode import unidecode

from comments.models import Commentable
from common.utils import groklinks
from common.utils.files import random_path
from common.utils.fuzzy_date import FuzzyDate
from common.utils.text import generate_search_title, strip_markup
from demoscene.models import DATE_PRECISION_CHOICES, ExternalLink, Releaser, TextFile
from productions.models import Production, Screenshot


class PartySeries(models.Model):
    name = models.CharField(max_length=255, unique=True)
    notes = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("party_series", args=[str(self.id)])

    def get_history_url(self):
        return reverse("party_series_history", args=[str(self.id)])

    @property
    def plaintext_notes(self):
        return strip_markup(self.notes)

    @property
    def active_external_links(self):
        return self.external_links.exclude(link_class__in=groklinks.ARCHIVED_LINK_TYPES)

    class Meta:
        verbose_name_plural = "Party series"
        ordering = ("name",)


class PartySeriesExternalLink(ExternalLink):
    party_series = models.ForeignKey(PartySeries, related_name="external_links", on_delete=models.CASCADE)
    link_types = groklinks.PARTY_SERIES_LINK_TYPES

    @property
    def subject(self):
        return self.party_series.name

    class Meta:
        unique_together = (("link_class", "parameter", "party_series"),)
        ordering = ["link_class"]


def party_share_image_upload_to(i, f):
    return random_path("party_share_images", f)


class Party(Commentable):
    party_series = models.ForeignKey(PartySeries, related_name="parties", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    tagline = models.CharField(max_length=255, blank=True)
    start_date_date = models.DateField()
    start_date_precision = models.CharField(max_length=1, choices=DATE_PRECISION_CHOICES)
    end_date_date = models.DateField()
    end_date_precision = models.CharField(max_length=1, choices=DATE_PRECISION_CHOICES)

    is_online = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)
    website = models.URLField(blank=True)

    sceneorg_compofolders_done = models.BooleanField(
        default=False,
        help_text=(
            "Indicates that all compos at this party have been matched up with the corresponding scene.org directory"
        ),
    )

    invitations = models.ManyToManyField("productions.Production", related_name="invitation_parties", blank=True)
    releases = models.ManyToManyField("productions.Production", related_name="release_parties", blank=True)

    share_image_file = models.ImageField(
        upload_to=party_share_image_upload_to,
        blank=True,
        width_field="share_image_file_width",
        height_field="share_image_file_height",
        help_text="Upload an image file to display when sharing this party page on social media",
    )
    share_image_file_width = models.IntegerField(editable=False, null=True)
    share_image_file_height = models.IntegerField(editable=False, null=True)
    share_image_file_url = models.CharField(max_length=255, blank=True, editable=False)
    share_screenshot = models.ForeignKey(
        "productions.Screenshot", related_name="+", blank=True, null=True, on_delete=models.SET_NULL
    )

    search_title = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    search_document = SearchVectorField(null=True, editable=False)

    search_result_template = "search/results/party.html"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # populate search_title from name
        if self.name:
            self.search_title = generate_search_title(self.name)

        super().save(*args, **kwargs)

        if self.share_image_file_url and not self.share_image_file:
            # clear the previous share_image_file_url field
            Party.objects.filter(pk=self.pk).update(share_image_file_url="")
            self.share_image_file_url = ""
        elif self.share_image_file and self.share_image_file.url != self.share_image_file_url:
            # update the share_image_file_url field with the URL from share_image_file
            Party.objects.filter(pk=self.pk).update(share_image_file_url=self.share_image_file.url)
            self.share_image_file_url = self.share_image_file.url

    def get_absolute_url(self):
        return reverse("party", args=[str(self.id)])

    def get_history_url(self):
        return reverse("party_history", args=[str(self.id)])

    @property
    def suffix(self):
        series_name = self.party_series.name
        if series_name == self.name and self.start_date:
            return self.start_date.date.year
        else:
            return re.sub(r"^" + re.escape(series_name) + r"\s+", "", self.name)

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

    def get_screenshots(self):
        compo_entry_prod_ids = Production.objects.filter(competition_placings__competition__party=self).values_list(
            "id", flat=True
        )
        invitation_prod_ids = self.invitations.values_list("id", flat=True)
        non_compo_release_prod_ids = self.releases.values_list("id", flat=True)
        prod_ids = list(compo_entry_prod_ids) + list(invitation_prod_ids) + list(non_compo_release_prod_ids)
        return Screenshot.objects.filter(production_id__in=prod_ids)

    def random_screenshot(self):
        screenshots = Screenshot.objects.filter(production__competition_placings__competition__party=self)
        try:
            return screenshots.order_by("?")[0]
        except IndexError:
            return None

    # return a FuzzyDate representing our best guess at when this party's competitions were held
    def default_competition_date(self):
        if self.end_date and self.end_date.precision == "d":
            # assume that competitions were held on the penultimate day of the party
            competition_day = self.end_date.date - datetime.timedelta(days=1)
            # ...but if that's in the future, use today instead
            if competition_day > datetime.date.today():
                competition_day = datetime.date.today()
            # ...and if that's before the (known exact) start date of the party, use that instead
            if self.start_date and self.start_date.precision == "d" and self.start_date.date > competition_day:
                competition_day = self.start_date.date
            return FuzzyDate(competition_day, "d")
        else:
            # we don't know this party's exact end date, so just use whatever precision of end date
            # we know (if indeed we have one at all)
            return self.end_date

    @property
    def plaintext_notes(self):
        return strip_markup(self.notes)

    @property
    def active_external_links(self):
        return self.external_links.exclude(link_class__in=groklinks.ARCHIVED_LINK_TYPES)

    # return the sceneorg.models.File instance for our best guess at the results textfile in this
    # party's folder on scene.org
    def sceneorg_results_file(self):
        from sceneorg.models import File as SceneOrgFile

        sceneorg_dirs = self.external_links.filter(link_class="SceneOrgFolder")
        for sceneorg_dir in sceneorg_dirs:
            for subpath in ["info/results.txt", "misc/results.txt", "results.txt"]:
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
        results_file.file.save(self.clean_name + ".txt", ContentFile(sceneorg_file.fetched_data()))
        # this also commits the ResultsFile record to the database

    @property
    def clean_name(self):
        """a name for this party that can be used in filenames (used to give results.txt files
        meaningful names on disk)"""
        return re.sub(r"\W+", "_", self.name.lower())

    @property
    def share_image_url(self):
        if self.share_image_file_url:
            return self.share_image_file_url
        elif self.share_screenshot:
            return self.share_screenshot.standard_url
        else:
            return "https://demozoo.org/static/images/fb-1200x627.png"

    @property
    def is_in_past(self):
        return self.end_date and self.end_date.date_range_end() < datetime.date.today()

    def index_components(self):
        return {
            "A": self.asciified_name,
            "B": self.tagline,
            "C": self.asciified_location + " " + self.plaintext_notes,
        }

    def get_competitions_with_prefetched_results(self, include_tags=False):
        production_prefetch_fields = [
            "production__author_nicks__releaser",
            "production__author_affiliation_nicks__releaser",
            "production__platforms",
            "production__types",
        ]
        if include_tags:
            production_prefetch_fields.append("production__tags")

        return self.competitions.prefetch_related(
            Prefetch(
                "placings",
                queryset=(
                    CompetitionPlacing.objects.order_by("position", "production_id")
                    .prefetch_related(*production_prefetch_fields)
                    .defer(
                        "production__notes",
                        "production__author_nicks__releaser__notes",
                        "production__author_affiliation_nicks__releaser__notes",
                    )
                ),
            )
        ).order_by("name", "id")

    class Meta:
        verbose_name_plural = "Parties"
        ordering = ("name",)
        indexes = [
            GinIndex(fields=["search_document"]),
        ]


class Organiser(models.Model):
    party = models.ForeignKey(Party, related_name="organisers", on_delete=models.CASCADE)
    releaser = models.ForeignKey(Releaser, related_name="parties_organised", on_delete=models.CASCADE)
    role = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return "%s - %s at %s" % (self.releaser.name, self.role, self.party.name)


class PartyExternalLink(ExternalLink):
    party = models.ForeignKey(Party, related_name="external_links", on_delete=models.CASCADE)
    link_types = groklinks.PARTY_LINK_TYPES

    @property
    def subject(self):
        return self.party.name

    class Meta:
        unique_together = (("link_class", "parameter", "party"),)
        ordering = ["link_class"]


class Competition(models.Model):
    party = models.ForeignKey(Party, related_name="competitions", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    shown_date_date = models.DateField(null=True, blank=True)
    shown_date_precision = models.CharField(max_length=1, blank=True, choices=DATE_PRECISION_CHOICES)
    platform = models.ForeignKey("platforms.Platform", blank=True, null=True, on_delete=models.SET_NULL)
    production_type = models.ForeignKey("productions.ProductionType", blank=True, null=True, on_delete=models.SET_NULL)

    def results(self):
        return self.placings.order_by("position")

    def __str__(self):
        try:
            return "%s %s" % (self.party.name, self.name)
        except Party.DoesNotExist:  # pragma: no cover
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
            self.shown_date_precision = ""

    shown_date = property(_get_shown_date, _set_shown_date)

    def get_absolute_url(self):
        return reverse("competition", args=[str(self.id)])

    def get_history_url(self):
        return reverse("competition_history", args=[str(self.id)])

    class Meta:
        ordering = ("party__name", "name")


class CompetitionPlacing(models.Model):
    competition = models.ForeignKey(Competition, related_name="placings", on_delete=models.CASCADE)
    production = models.ForeignKey(
        "productions.Production", related_name="competition_placings", on_delete=models.CASCADE
    )
    ranking = models.CharField(max_length=32, blank=True)
    position = models.IntegerField()
    score = models.CharField(max_length=32, blank=True)

    @property
    def json_data(self):
        if self.production.is_stable_for_competitions():
            return {
                "id": self.id,
                "ranking": self.ranking,
                "score": self.score,
                "production": {
                    "id": self.production.id,
                    "title": self.production.title,
                    "byline": self.production.byline_string,
                    "url": self.production.get_absolute_url(),
                    "platform_name": self.production.platform_name,
                    "production_type_name": self.production.type_name,
                    "stable": True,
                },
            }
        else:
            byline_search = self.production.byline_search()
            return {
                "id": self.id,
                "ranking": self.ranking,
                "score": self.score,
                "production": {
                    "id": self.production.id,
                    "title": self.production.title,
                    "platform": self.production.platforms.all()[0].id if self.production.platforms.all() else None,
                    "production_type": self.production.types.all()[0].id if self.production.types.all() else None,
                    # it's OK to reduce platform / prodtype to a single value, because unstable productions
                    # can only ever have one (adding multiple on the production edit page would make them stable)
                    "byline": {
                        "search_term": byline_search.search_term,
                        "author_matches": byline_search.author_matches_data,
                        "affiliation_matches": byline_search.affiliation_matches_data,
                    },
                    "stable": False,
                },
            }

    def __str__(self):
        try:
            return str(self.production)
        except Production.DoesNotExist:  # pragma: no cover
            return "(CompetitionPlacing)"


class ResultsFile(TextFile):
    party = models.ForeignKey(Party, related_name="results_files", on_delete=models.CASCADE)
    file = models.FileField(storage=FileSystemStorage(), upload_to="results", blank=True)
