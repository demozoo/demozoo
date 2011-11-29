from django.db import models
import urllib

class Directory(models.Model):
	path = models.CharField(max_length=255)
	is_deleted = models.BooleanField(default=False)
	last_seen_at = models.DateTimeField()
	last_spidered_at = models.DateTimeField(null=True, blank=True)
	parent = models.ForeignKey('Directory', related_name = 'subdirectories', null=True, blank=True)
	
	def __unicode__(self):
		return self.path
	
	@property
	def web_url(self):
		return "http://www.scene.org/dir.php?dir=%s" % urllib.quote(self.path.encode("utf-8"))

class File(models.Model):
	path = models.CharField(max_length=255)
	is_deleted = models.BooleanField(default=False)
	last_seen_at = models.DateTimeField()
	directory = models.ForeignKey(Directory, related_name = 'files')
	
	def __unicode__(self):
		return self.path
	
	@property
	def web_url(self):
		return "http://www.scene.org/file.php?file=%s&fileinfo" % urllib.quote(self.path.encode("utf-8"))
