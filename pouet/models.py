from django.db import models


class Group(models.Model):
    pouet_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    demozoo_id = models.IntegerField(null=True, blank=True)
    last_seen_at = models.DateTimeField()


class Platform(models.Model):
    pouet_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)


class ProductionType(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)


class Production(models.Model):
    pouet_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    download_url = models.TextField()
    groups = models.ManyToManyField(Group, related_name='productions')
    platforms = models.ManyToManyField(Platform, related_name='productions')
    types = models.ManyToManyField(ProductionType, related_name='productions')
    vote_up_count = models.IntegerField(null=True, blank=True)
    vote_pig_count = models.IntegerField(null=True, blank=True)
    vote_down_count = models.IntegerField(null=True, blank=True)
    cdc_count = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)
    last_seen_at = models.DateTimeField()


class DownloadLink(models.Model):
    production = models.ForeignKey(Production, related_name='download_links', on_delete=models.CASCADE)
    url = models.TextField()
    link_type = models.CharField(max_length=255)


class GroupMatchInfo(models.Model):
    releaser = models.OneToOneField('demoscene.Releaser', on_delete=models.CASCADE)
    matched_production_count = models.IntegerField()
    unmatched_demozoo_production_count = models.IntegerField()
    unmatched_pouet_production_count = models.IntegerField()
