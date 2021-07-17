from django.db import models
from django.utils.functional import cached_property

from demoscene.models import Nick
from parties.models import Party


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


class Entry(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='entries')
    nick = models.ForeignKey(
        Nick, blank=True, null=True, on_delete=models.CASCADE, related_name='tournament_entries'
    )
    name = models.CharField(max_length=255, blank=True, help_text="Only if nick is empty")
    ranking = models.CharField(max_length=32, blank=True)
    position = models.IntegerField()
    score = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ['position']

    def __str__(self) -> str:
        return self.nick.name if self.nick else self.name


ROLES = [
    ('commentary', 'Commentary'),
    ('dj_set', 'DJ set'),
    ('live_music', 'Live music'),
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
