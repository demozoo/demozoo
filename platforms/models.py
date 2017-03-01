from django.db import models

from lib.model_thumbnail import ModelWithThumbnails
from demoscene.models import Releaser
from demoscene.utils.files import random_path


def photo_original_upload_to(i, f):
    return random_path('platform_photos/original', f)


def thumbnail_upload_to(i, f):
    return random_path('platform_photos/thumb', f)


class Platform(ModelWithThumbnails):
	name = models.CharField(max_length=255)
	intro_text = models.TextField(blank=True)

	photo = models.ImageField(
		null=True, blank=True,
		upload_to=photo_original_upload_to,
		width_field='photo_width', height_field='photo_height')
	photo_width = models.IntegerField(null=True, blank=True, editable=False)
	photo_height = models.IntegerField(null=True, blank=True, editable=False)

	thumbnail = models.ImageField(
		null=True, blank=True,
		upload_to=thumbnail_upload_to,
		editable=False, width_field='thumbnail_width', height_field='thumbnail_height')
	thumbnail_width = models.IntegerField(null=True, blank=True, editable=False)
	thumbnail_height = models.IntegerField(null=True, blank=True, editable=False)

	def save(self, *args, **kwargs):
		if self.photo:
			Platform.generate_thumbnail(self.photo, self.thumbnail, (135, 90), crop=True)
		super(Platform, self).save(*args, **kwargs)

	def __unicode__(self):
		return self.name

	def random_active_groups(self):
		return Releaser.objects.raw('''
			SELECT * FROM (
				SELECT group_id AS id, group_name AS title, MAX(release_date) FROM (

					-- all groups named as authors of prods on this platform
					SELECT
						demoscene_releaser.id AS group_id,
						demoscene_releaser.name AS group_name,
						productions_production.release_date_date AS release_date
					FROM
						productions_production
						INNER JOIN productions_production_platforms ON (
							productions_production.id = productions_production_platforms.production_id
							AND productions_production_platforms.platform_id = %s
						)
						INNER JOIN productions_production_author_nicks ON (
							productions_production.id = productions_production_author_nicks.production_id
						)
						INNER JOIN demoscene_nick ON (
							productions_production_author_nicks.nick_id = demoscene_nick.id
						)
						INNER JOIN demoscene_releaser ON (
							demoscene_nick.releaser_id = demoscene_releaser.id
							AND is_group = 't'
						)
					WHERE
						productions_production.release_date_date IS NOT NULL

					UNION

					-- all groups named as author affiliations of prods on this platform
					SELECT
						demoscene_releaser.id AS group_id,
						demoscene_releaser.name AS group_name,
						productions_production.release_date_date AS release_date
					FROM
						productions_production
						INNER JOIN productions_production_platforms ON (
							productions_production.id = productions_production_platforms.production_id
							AND productions_production_platforms.platform_id = %s
						)
						INNER JOIN productions_production_author_affiliation_nicks ON (
							productions_production.id = productions_production_author_affiliation_nicks.production_id
						)
						INNER JOIN demoscene_nick ON (
							productions_production_author_affiliation_nicks.nick_id = demoscene_nick.id
						)
						INNER JOIN demoscene_releaser ON (
							demoscene_nick.releaser_id = demoscene_releaser.id
							AND is_group = 't'
						)
					WHERE
						productions_production.release_date_date IS NOT NULL

				) AS grps

				GROUP BY group_id, group_name
				ORDER BY MAX(release_date) DESC
				LIMIT 100
			) AS topgroups
			ORDER BY RANDOM()
			LIMIT 10;
		''', (self.id, self.id))

	class Meta:
		ordering = ['name']
