from django.db import models

from common.utils.text import generate_search_title


class Author(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    real_name = models.CharField(blank=True, max_length=255)
    real_name_hidden = models.BooleanField(default=False)
    is_group = models.BooleanField()
    country_code = models.CharField(max_length=5, blank=True)
    is_company = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_member_ids(self):
        return Author.objects.filter(group_memberships__group=self).values_list('janeway_id', flat=True)

    def get_member_clean_names(self):
        """
        return a list of cleaned versions of all names used by members of this group
        (excluding ones of <=3 letters)
        """
        return list(
            filter(lambda s: len(s) > 3, [
                generate_search_title(name.name)
                for name in Name.objects.filter(author__group_memberships__group=self)
            ])
        )

    def get_group_ids(self):
        return Author.objects.filter(
            is_group=True, member_memberships__member=self
        ).values_list('janeway_id', flat=True)

    def get_group_clean_names(self):
        """
        return a list of cleaned versions of all names of groups this scener is a member of
        (excluding ones of <=3 letters)
        """
        return list(
            filter(lambda s: len(s) > 3, [
                generate_search_title(name.name)
                for name in Name.objects.filter(author__is_group=True, author__member_memberships__member=self)
            ])
        )


class Name(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='names')
    janeway_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, blank=True)


class Membership(models.Model):
    group = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='member_memberships')
    member = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='group_memberships')
    since = models.DateField(blank=True, null=True)
    until = models.DateField(blank=True, null=True)
    founder = models.BooleanField(default=False)


SUPERTYPE_CHOICES = (
    ('production', 'Production'),
    ('graphics', 'Graphics'),
    ('music', 'Music'),
)

PLATFORM_CHOICES = (
    ('ocs', 'Amiga OCS/ECS'),
    ('aga', 'Amiga AGA'),
    ('ppc', 'Amiga PPC/RTG'),
)

DATE_PRECISION_CHOICES = (
    ('d', 'Day'),
    ('m', 'Month'),
    ('y', 'Year'),
)


class Release(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    supertype = models.CharField(max_length=20, choices=SUPERTYPE_CHOICES)
    author_names = models.ManyToManyField(Name, related_name='authored_releases')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, blank=True)
    release_date_date = models.DateField(null=True, blank=True)
    release_date_precision = models.CharField(max_length=1, blank=True, choices=DATE_PRECISION_CHOICES)


class ReleaseType(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='types')
    type_name = models.CharField(max_length=255)


class Credit(models.Model):
    janeway_id = models.IntegerField(db_index=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='credits')
    name = models.ForeignKey(Name, on_delete=models.CASCADE, related_name='credits')
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)


class DownloadLink(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='download_links')
    url = models.URLField(max_length=255)
    comment = models.TextField(blank=True)


class PackContent(models.Model):
    pack = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='pack_contents')
    content = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='packed_in')


class SoundtrackLink(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='soundtrack_links')
    soundtrack = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='appearances_as_soundtrack')


class Screenshot(models.Model):
    janeway_id = models.IntegerField()  # non-unique, as an entry on Janeway can correspond to a range of screenshots
    suffix = models.CharField(blank=True, max_length=5)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='screenshots')
    url = models.URLField(max_length=255)
    comment = models.TextField(blank=True)


class AuthorMatchInfo(models.Model):
    releaser = models.OneToOneField('demoscene.Releaser', on_delete=models.CASCADE)
    matched_production_count = models.IntegerField()
    unmatched_demozoo_production_count = models.IntegerField()
    unmatched_janeway_production_count = models.IntegerField()
