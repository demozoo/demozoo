from django.db import models
from django.urls import reverse


class BBS(models.Model):
    name = models.CharField(max_length=255)

    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)

    bbstros = models.ManyToManyField('productions.Production', related_name='bbses', blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('bbs', args=[self.id])

    def get_absolute_edit_url(self):
        return reverse('bbs', args=[self.id])

    def get_history_url(self):
        return reverse('bbs_history', args=[self.id])

    def is_referenced(self):
        """
        Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
        that should prevent its deletion
        """
        return self.bbstros.exists() or self.staff.exists()

    class Meta:
        verbose_name_plural = 'BBSes'


OPERATOR_TYPES = [
    ('sysop', 'Sysop'),
    ('co-sysop', 'Co-Sysop'),
]


class Operator(models.Model):
    bbs = models.ForeignKey(BBS, related_name='staff', on_delete=models.CASCADE)
    releaser = models.ForeignKey('demoscene.Releaser', related_name='bbses_operated', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=OPERATOR_TYPES)

    def __str__(self):
        return "%s - %s of %s" % (self.releaser.name, self.role, self.bbs.name)
