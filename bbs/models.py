from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from strip_markup import strip_markup
from taggit.managers import TaggableManager
from unidecode import unidecode

from demoscene.models import TextFile
from demoscene.utils.text import generate_search_title


class BBS(models.Model):
    name = models.CharField(max_length=255)

    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)

    bbstros = models.ManyToManyField('productions.Production', related_name='bbses', blank=True)

    tags = TaggableManager(blank=True)

    search_title = models.CharField(max_length=255, blank=True, editable=False, db_index=True)
    search_document = SearchVectorField(null=True, editable=False)

    search_result_template = 'search/results/bbs.html'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_title = generate_search_title(self.name)

        super().save(*args, **kwargs)

        # ensure that a Name with matching name exists for this BBS
        name, created = Name.objects.get_or_create(bbs=self, name=self.name)

    @property
    def primary_name(self):
        return self.names.get(name=self.name)

    def get_absolute_url(self):
        return reverse('bbs', args=[self.id])

    def get_history_url(self):
        return reverse('bbs_history', args=[self.id])

    def is_referenced(self):
        """
        Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
        that should prevent its deletion
        """
        return self.bbstros.exists() or self.staff.exists() or self.affiliations.exists()

    @property
    def asciified_name(self):
        return unidecode(self.name)

    @property
    def asciified_location(self):
        return self.location and unidecode(self.location)

    @property
    def all_names_string(self):
        all_names = [name.name for name in self.names.all()]
        return ', '.join(all_names)

    @property
    def asciified_all_names_string(self):
        return unidecode(self.all_names_string)

    @property
    def plaintext_notes(self):
        return strip_markup(self.notes)

    @property
    def tags_string(self):
        return ', '.join([tag.name for tag in self.tags.all()])

    def index_components(self):
        return {
            'A': self.asciified_all_names_string,
            'C': self.asciified_location + ' ' + self.tags_string + ' ' + self.plaintext_notes,
        }

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'BBSes'
        indexes = [
            GinIndex(fields=['search_document']),
        ]


class Name(models.Model):
    bbs = models.ForeignKey(BBS, related_name='names', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_name = self.name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # update BBS name if it matches this nick's previous name
        if self.id is not None:
            super().save(*args, **kwargs)  # Call the original save() method
            if (self._original_name == self.bbs.name) and (self._original_name != self.name):
                self.bbs.name = self.name
                self.bbs.save()
        else:
            super().save(*args, **kwargs)  # Call the original save() method

    def is_primary_name(self):
        return (self.bbs.name == self.name)

    class Meta:
        unique_together = ("bbs", "name")
        ordering = ['name']


OPERATOR_TYPES = [
    ('sysop', 'Sysop'),
    ('co-sysop', 'Co-Sysop'),
]


class Operator(models.Model):
    bbs = models.ForeignKey(BBS, related_name='staff', on_delete=models.CASCADE)
    releaser = models.ForeignKey('demoscene.Releaser', related_name='bbses_operated', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=OPERATOR_TYPES)
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return "%s - %s of %s" % (self.releaser.name, self.role, self.bbs.name)


AFFILIATION_TYPES = [
    ('010-whq', 'WHQ'),
    ('015-ehq', 'EHQ'),
    ('020-hq', 'HQ'),
    ('030-memberboard', 'Memberboard'),
    ('040-distsite', 'Distsite'),
]


class Affiliation(models.Model):
    bbs = models.ForeignKey(BBS, related_name='affiliations', on_delete=models.CASCADE)
    group = models.ForeignKey('demoscene.Releaser', related_name='bbs_affiliations', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=AFFILIATION_TYPES, blank=True)

    def __str__(self):
        if self.role:
            return "%s - %s for %s" % (self.bbs.name, self.get_role_display(), self.group.name)
        else:
            return "%s affiliated with %s" % (self.group.name, self.bbs.name)


class TextAd(TextFile):
    bbs = models.ForeignKey(BBS, related_name='text_ads', on_delete=models.CASCADE)
    file = models.FileField(upload_to='bbs_ads', blank=True)
