import hashlib
import random
import re
from collections import defaultdict

from django.db import models
from django.utils.functional import cached_property

from common.utils import groklinks
from demoscene.models import ExternalLink, Nick
from parties.models import Party
from screenshots.models import PILConvertibleImage, ThumbnailMixin
from screenshots.processing import upload_to_s3
from screenshots.tasks import create_basename


class Tournament(models.Model):
    source_file_name = models.CharField(max_length=255, unique=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='tournaments')
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = [
            ('party', 'name')
        ]

    def __str__(self) -> str:
        return "%s at %s" % (self.name, self.party.name)

    def get_absolute_url(self):
        return self.party.get_absolute_url() + ("#tournament_%d" % self.id)

    @property
    def livecode_url(self):
        html_file_name = re.sub(r'\.json$', '.html', self.source_file_name)
        return 'https://livecode.demozoo.org/event/%s#mc' % html_file_name


class TournamentExternalLink(ExternalLink):
    tournament = models.ForeignKey(Tournament, related_name='external_links', on_delete=models.CASCADE)
    link_types = groklinks.TOURNAMENT_LINK_TYPES

    @property
    def subject(self):
        return "%s %s" % (self.tournament.party.name, self.tournament.name)

    class Meta:
        unique_together = (
            ('link_class', 'parameter', 'tournament'),
        )
        ordering = ['link_class']


class Phase(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=255, blank=True)
    position = models.IntegerField()

    @cached_property
    def has_rankings(self):
        return any(entry.ranking for entry in self.entries.all())

    @cached_property
    def has_scores(self):
        return any(entry.score for entry in self.entries.all())

    class Meta:
        ordering = ['position']

    def __str__(self) -> str:
        return self.name

    @property
    def party_scoped_name(self):
        if self.name:
            return "%s %s" % (self.tournament.name, self.name)
        else:
            return "%s %s" % (self.tournament.party.name, self.tournament.name)


class PhaseExternalLink(ExternalLink):
    phase = models.ForeignKey(Phase, related_name='external_links', on_delete=models.CASCADE)
    link_types = groklinks.TOURNAMENT_LINK_TYPES

    @property
    def subject(self):
        return self.phase.party_scoped_name

    class Meta:
        unique_together = (
            ('link_class', 'parameter', 'phase'),
        )
        ordering = ['link_class']


class Entry(ThumbnailMixin, models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='entries')
    nick = models.ForeignKey(
        Nick, blank=True, null=True, on_delete=models.CASCADE, related_name='tournament_entries'
    )
    name = models.CharField(max_length=255, blank=True, help_text="Only if nick is empty")
    ranking = models.CharField(max_length=32, blank=True)
    position = models.IntegerField()
    score = models.CharField(max_length=32, blank=True)
    source_file = models.CharField(max_length=255, blank=True)

    thumbnail_url = models.CharField(max_length=255, blank=True, editable=False)
    thumbnail_width = models.IntegerField(null=True, blank=True, editable=False)
    thumbnail_height = models.IntegerField(null=True, blank=True, editable=False)
    original_image_sha1 = models.CharField(max_length=40, blank=True, editable=False)

    class Meta:
        ordering = ['position']

    @property
    def author_name(self):
        return self.nick.name if self.nick else self.name

    def __str__(self) -> str:
        return self.author_name

    def set_screenshot(self, filename):
        f = open(filename, 'rb')
        sha1 = hashlib.sha1(f.read()).hexdigest()
        if sha1 == self.original_image_sha1:
            f.close()
            return False

        self.original_image_sha1 = sha1
        f.seek(0)
        img = PILConvertibleImage(f, name_hint=filename)
        thumb, thumb_size, thumb_format = img.create_thumbnail((200, 150))
        basename = create_basename(self.id)
        self.thumbnail_url = upload_to_s3(thumb, 'tournament_screens/t/' + basename + thumb_format)
        self.thumbnail_width, self.thumbnail_height = thumb_size
        f.close()
        return True

    @property
    def source_code_url(self):
        if self.source_file:
            if self.source_file.startswith('/'):
                return "https://livecode.demozoo.org%s" % self.source_file
            else:
                return self.source_file

    @property
    def party_scoped_name(self):
        if self.phase.name:
            return "%s's %s %s entry" % (
                self.author_name, self.phase.tournament.name, self.phase.name
            )
        else:
            return "%s's %s entry" % (
                self.author_name, self.phase.tournament.name
            )

    @staticmethod
    def select_screenshots_for_releaser_id(releaser_id):
        """
        Given a releaser id, return a dict where the keys are IDs of tournaments that the
        releaser has at least one entry with a screenshot in, and the value is a randomly-chosen
        entry with a screenshot in that tournament.
        """
        tournament_and_entry_ids = (
            Entry.objects.exclude(thumbnail_url='')
            .filter(nick__releaser_id=releaser_id)
            .select_related('phase')
            .values_list('phase__tournament_id', 'id')
        )

        entries_by_tournament_id = defaultdict(list)
        for (tournament_id, entry_id) in tournament_and_entry_ids:
            entries_by_tournament_id[tournament_id].append(entry_id)

        chosen_entry_ids = [
            random.choice(entry_id_set)
            for entry_id_set in entries_by_tournament_id.values()
        ]

        return {
            entry.phase.tournament_id: entry
            for entry in Entry.objects.filter(id__in=chosen_entry_ids).select_related('phase')
        }


class EntryExternalLink(ExternalLink):
    entry = models.ForeignKey(Entry, related_name='external_links', on_delete=models.CASCADE)
    link_types = groklinks.TOURNAMENT_LINK_TYPES

    @property
    def subject(self):
        return self.entry.party_scoped_name

    class Meta:
        unique_together = (
            ('link_class', 'parameter', 'entry'),
        )
        ordering = ['link_class']


ROLES = [
    ('commentary', 'Commentary'),
    ('dj_set', 'DJ set'),
    ('live_music', 'Live music'),
    ('vj', 'VJ'),
]


class PhaseStaffMember(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='staff')
    nick = models.ForeignKey(
        Nick, blank=True, null=True, on_delete=models.CASCADE, related_name='tournament_staff'
    )
    name = models.CharField(max_length=255, blank=True, help_text="Only if nick is empty")
    role = models.CharField(max_length=50, choices=ROLES)

    class Meta:
        ordering = ['role']
