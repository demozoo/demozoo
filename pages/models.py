from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    body = models.TextField()
    
    def __str__(self):
        return self.title
