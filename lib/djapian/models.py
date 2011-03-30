from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.encoding import smart_str

from datetime import datetime

from djapian import utils

class ChangeManager(models.Manager):
    def create(self, object, action, **kwargs):
        ct = ContentType.objects.get_for_model(object.__class__)
        pk = smart_str(object.pk)

        try:
            old_change = self.get(
                content_type=ct,
                object_id=pk
            )
            if old_change.action=="add":
                if action=="edit":
                    old_change.save()
                    return old_change
                elif action=="delete":
                    old_change.delete()
                    return None
            old_change.delete()
        except self.model.DoesNotExist:
            old_change = self.model(content_type=ct, object_id=pk)

        old_change.action = action
        old_change.save()

        return old_change


class Change(models.Model):
    ACTIONS = (
        ("add", "object added"),
        ("edit", "object edited"),
        ("delete", "object deleted"),
    )

    content_type = models.ForeignKey(ContentType, db_index=True)
    object_id = models.CharField(max_length=150)

    date = models.DateTimeField(default=datetime.now)
    action = models.CharField(max_length=6, choices=ACTIONS)

    object = generic.GenericForeignKey()

    objects = ChangeManager()

    def __unicode__(self):
        return u'%s %s#%s on %s' % (
            self.action,
            self.content_type,
            self.object_id,
            self.date
        )

    def save(self):
        self.date = datetime.now()

        super(Change, self).save()

    class Meta:
        unique_together = [("content_type", "object_id")]
