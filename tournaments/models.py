from django.db import models

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
