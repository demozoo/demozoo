import hashlib
import re

from django.db import models
from django.utils.functional import cached_property

from demoscene.models import Nick
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


class Entry(ThumbnailMixin, models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='entries')
    nick = models.ForeignKey(
        Nick, blank=True, null=True, on_delete=models.CASCADE, related_name='tournament_entries'
    )
    name = models.CharField(max_length=255, blank=True, help_text="Only if nick is empty")
    ranking = models.CharField(max_length=32, blank=True)
    position = models.IntegerField()
    score = models.CharField(max_length=32, blank=True)

    thumbnail_url = models.CharField(max_length=255, blank=True, editable=False)
    thumbnail_width = models.IntegerField(null=True, blank=True, editable=False)
    thumbnail_height = models.IntegerField(null=True, blank=True, editable=False)
    original_image_sha1 = models.CharField(max_length=40, blank=True, editable=False)

    class Meta:
        ordering = ['position']

    def __str__(self) -> str:
        return self.nick.name if self.nick else self.name

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
