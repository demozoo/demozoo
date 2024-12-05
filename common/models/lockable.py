from django.db import models


class Lockable(models.Model):
    locked = models.BooleanField(default=False, editable=False)

    def editable_by_user(self, user):
        return user.is_authenticated and ((not self.locked) or user.is_staff)

    class Meta:
        abstract = True
