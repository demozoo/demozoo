from django.db import models


class Author(models.Model):
	janeway_id = models.IntegerField()
	name = models.CharField(max_length=255)
	real_name = models.CharField(blank=True, max_length=255)
	real_name_hidden = models.BooleanField(default=False)
	is_group = models.BooleanField()

	def __str__(self):
		return self.name


class Name(models.Model):
	author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='names')
	janeway_id = models.IntegerField()
	name = models.CharField(max_length=255)
	abbreviation = models.CharField(max_length=255, blank=True)


class Membership(models.Model):
	group = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='member_memberships')
	member = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='group_memberships')
	since = models.DateField(blank=True, null=True)
	until = models.DateField(blank=True, null=True)
	founder = models.BooleanField(default=False)
