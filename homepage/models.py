from django.db import models

from demoscene.utils.files import random_path


class Banner(models.Model):
    banner_image = models.ForeignKey(
        'BannerImage', null=True, blank=True, related_name='+',
        on_delete=models.SET_NULL,  # don't want deletion to cascade to the banner if image is deleted
    )
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True)
    url = models.CharField(max_length=255, verbose_name="URL")
    hide_text = models.BooleanField(
        default=False,
        help_text="Instead of displaying text, use it as fallback text for people who can't see the image"
    )

    show_for_anonymous_users = models.BooleanField(default=True)
    show_for_logged_in_users = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


def banner_image_upload_to(i, f):
    return random_path('homepage_banners', f)


class BannerImage(models.Model):
    image = models.ImageField(
        upload_to=banner_image_upload_to,
        width_field='image_width', height_field='image_height',
        help_text='Will be cropped to 2.5 : 1 aspect ratio. Recommended size: 832x333')
    image_width = models.IntegerField(editable=False)
    image_height = models.IntegerField(editable=False)
    image_url = models.CharField(max_length=255, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # following the call to super(), self.image.url is now defined and can be used
        # to populate image_url - but we'll do this via `update` to avoid another call to save
        BannerImage.objects.filter(pk=self.pk).update(image_url=self.image.url)

    # method for displaying image in admin listings
    def image_tag(self):
        return '<img src="%s" width="400" alt="" />' % self.image_url
    image_tag.allow_tags = True

    def __str__(self):
        return self.image.name


class NewsStory(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    image = models.ForeignKey(
        'NewsImage', null=True, blank=True, related_name='+',
        on_delete=models.SET_NULL,  # don't want deletion to cascade to the news story if image is deleted
    )
    is_public = models.BooleanField(blank=True, default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'News stories'


def news_image_upload_to(i, f):
    return random_path('news_images', f)


class NewsImage(models.Model):
    image = models.ImageField(
        upload_to=news_image_upload_to,
        width_field='image_width', height_field='image_height',
        help_text='Recommended size: 100x100')
    image_width = models.IntegerField(editable=False)
    image_height = models.IntegerField(editable=False)
    image_url = models.CharField(max_length=255, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # following the call to super(), self.image.url is now defined and can be used
        # to populate image_url - but we'll do this via `update` to avoid another call to save
        NewsImage.objects.filter(pk=self.pk).update(image_url=self.image.url)

    # method for displaying image in admin listings
    def image_tag(self):
        return '<img src="%s" width="100" alt="" />' % self.image_url
    image_tag.allow_tags = True

    def __str__(self):
        return self.image.name
