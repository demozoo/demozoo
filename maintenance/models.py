from django.db import models


class Exclusion(models.Model):
    record_id = models.IntegerField()
    report_name = models.CharField(max_length=255)


class UntrustedLinkIdentifier(models.Model):
    url_part = models.CharField(
        max_length=64,
        help_text="Enter identifier for an untrusted link. This is usually a part of an URL for example 'goo.gl'. " \
                  "You can also specify 'negative' identifiers like this: untergrund.net!web.archive.org will match " \
                  "any URL that contains 'untergrund.net' but does not contain 'web.archive.org'."
    )

    def __str__(self):
        return self.url_part
