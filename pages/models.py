from django.db import models

class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    body = models.TextField()
    
    def __unicode__(self):
        return self.title
