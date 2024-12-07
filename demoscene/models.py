import datetime
import hashlib
import re
from collections import OrderedDict as SortedDict
from io import StringIO

from ansipants import ANSIDecoder
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models, transaction
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from unidecode import unidecode

from common.models import Lockable, PrefetchSnoopingMixin
from common.utils import groklinks
from common.utils.text import generate_search_title, strip_markup


DATE_PRECISION_CHOICES = [
    ("d", "Day"),
    ("m", "Month"),
    ("y", "Year"),
]


class Releaser(PrefetchSnoopingMixin, Lockable):
    name = models.CharField(max_length=255)
    is_group = models.BooleanField(db_index=True)
    notes = models.TextField(blank=True)

    demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name="Demozoo v0 ID")

    location = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geonames_id = models.BigIntegerField(null=True, blank=True)

    first_name = models.CharField(max_length=255, blank=True)
    surname = models.CharField(max_length=255, blank=True)
    real_name_note = models.TextField(
        default="",
        blank=True,
        verbose_name="Permission note",
        help_text="Details of any correspondence / decision about whether this name should be public",
    )

    hide_from_search_engines = models.BooleanField(default=False)

    data_source = models.CharField(max_length=32, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    search_document = SearchVectorField(null=True, editable=False)

    def save(self, *args, **kwargs):
        # auto-populate updated_at; this will only happen on creation
        # because it's a non-null field at the db level
        if self.updated_at is None:
            self.updated_at = datetime.datetime.now()

        with transaction.atomic():
            super().save(*args, **kwargs)  # Call the "real" save() method

            # ensure that a Nick with matching name exists for this releaser
            nick, created = Nick.objects.get_or_create(releaser=self, name=self.name)

    def __str__(self):
        return self.name

    def search_result_template(self):
        return "search/results/group.html" if self.is_group else "search/results/scener.html"

    def get_absolute_url(self):
        if self.is_group:
            return reverse("group", args=[str(self.id)])
        else:
            return reverse("scener", args=[str(self.id)])

    def get_history_url(self):
        if self.is_group:
            return reverse("group_history", args=[str(self.id)])
        else:
            return reverse("scener_history", args=[str(self.id)])

    def productions(self):
        from productions.models import Production

        return Production.objects.filter(author_nicks__in=list(self.nicks.all()))

    def member_productions(self):
        # Member productions are those which list this group in the 'affiliations' portion of the byline,
        # OR the author is a SUBGROUP of this group (regardless of whether this parent group is named as an
        # affiliation).
        from productions.models import Production

        subgroup_nick_ids = list(
            Nick.objects.filter(releaser__is_group=True, releaser__group_memberships__group=self).values_list(
                "id", flat=True
            )
        )
        subgroup_prod_ids = set(
            Production.objects.filter(author_nicks__in=subgroup_nick_ids).values_list("id", flat=True)
        )
        affiliation_prod_ids = set(
            Production.objects.filter(author_affiliation_nicks__in=list(self.nicks.all())).values_list("id", flat=True)
        )

        return Production.objects.filter(id__in=(subgroup_prod_ids | affiliation_prod_ids))

    def credits(self):
        from productions.models import Credit

        return Credit.objects.select_related("nick").filter(nick__releaser=self)

    def get_tournament_participations(self):
        from tournaments.models import Tournament

        return (
            Tournament.objects.filter(phases__entries__nick__releaser_id=self.id)
            .distinct()
            .order_by("-party__start_date_date")
        )

    def groups(self):
        return [
            membership.group for membership in self.group_memberships.select_related("group").order_by("group__name")
        ]

    def current_groups(self, prefetch_nicks=False):
        if self.has_prefetched("group_memberships"):
            # do the is_current filter in Python to avoid another SQL query
            return [membership.group for membership in self.group_memberships.all() if membership.is_current]
        else:
            current_memberships = (
                self.group_memberships.filter(is_current=True)
                .select_related("group")
                .only("member", "group", "is_current", "group__name")
                .order_by("group__name")
            )
            if prefetch_nicks:
                current_memberships = current_memberships.prefetch_related("group__nicks")
            return [membership.group for membership in current_memberships]

    def members(self):
        return [
            membership.member
            for membership in self.member_memberships.select_related("member").order_by("member__name")
        ]

    @property
    def active_external_links(self):
        return self.external_links.exclude(link_class__in=groklinks.ARCHIVED_LINK_TYPES)

    def name_with_affiliations(self):
        groups = self.current_groups(prefetch_nicks=True)

        if groups:
            if sum([len(group.name) for group in groups]) >= 20:
                # abbreviate where possible
                group_names = [(group.abbreviation or group.name) for group in groups]
            else:
                # use full group names - not too long
                group_names = [group.name for group in groups]
            return "%s / %s" % (self.name, " ^ ".join(group_names))
        else:
            return self.name

    @property
    def primary_nick(self):
        if self.has_prefetched("nicks"):
            # filter the nicks list in Python to avoid another SQL query
            matching_nicks = [n for n in self.nicks.all() if n.name == self.name]
            if not matching_nicks:
                raise Nick.DoesNotExist()
            elif len(matching_nicks) > 1:
                raise Nick.MultipleObjectsReturned()
            else:
                return matching_nicks[0]
        else:
            # find the nick which matches this releaser by name
            # (will die loudly if one doesn't exist. So let's hope it does, eh?)
            return self.nicks.get(name=self.name)

    @property
    def abbreviation(self):
        return self.primary_nick.abbreviation

    @property
    def alternative_nicks(self):
        # A queryset of all nicks except the primary one
        return self.nicks.exclude(name=self.name)

    @property
    def real_name(self):
        if self.first_name or self.surname:
            return ("%s %s" % (self.first_name, self.surname)).strip()
        else:
            return None

    @property
    def asciified_real_name(self):
        real_name = self.real_name
        return real_name and unidecode(real_name)

    def has_real_name(self):
        return bool(self.first_name or self.surname)

    @property
    def all_names_string(self):
        if self.has_prefetched("nicks"):
            all_names = [nv.name for nick in self.nicks.all() for nv in nick.variants.all()]
        else:
            all_names = [nv.name for nv in NickVariant.objects.filter(nick__releaser=self)]
        return ", ".join(all_names)

    @property
    def asciified_all_names_string(self):
        return unidecode(self.all_names_string)

    @property
    def asciified_location(self):
        return self.location and unidecode(self.location)

    # Determine whether or not this releaser is referenced in any external records (credits, authorships etc)
    # that should prevent its deletion
    def is_referenced(self):
        return (
            self.credits().count()
            # A group with members can't be deleted, although a scener with groups can. Seems to make sense...
            or self.member_memberships.count()
            or self.productions().count()
            or self.member_productions().count()
        )

    def can_be_converted_to_group(self):
        return not self.first_name and not self.surname and not self.location

    def can_be_converted_to_scener(self):
        # don't allow converting a group to scener if it has members or member productions
        return not self.members() and not self.member_productions()

    @property
    def plaintext_notes(self):
        return strip_markup(self.notes)

    def index_components(self):
        return {
            "A": self.asciified_all_names_string,
            "B": self.asciified_real_name,
            "C": self.asciified_location + " " + self.plaintext_notes,
        }

    class Meta:
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["search_document"]),
        ]
        permissions = (("change_releaser_real_names", "Can change non-public real names"),)


class Nick(PrefetchSnoopingMixin, models.Model):
    releaser = models.ForeignKey(Releaser, related_name="nicks", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(
        max_length=255,
        blank=True,
        help_text="(optional - only if there's one that's actively being used. Don't just make one up!)",
    )
    differentiator = models.CharField(
        max_length=32,
        blank=True,
        help_text="hint text to distinguish from other groups/sceners with the same name - e.g. platform or country",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_written_nick_variant_list = False
        self._nick_variant_list = None

    def __str__(self):
        return self.name

    @staticmethod
    def from_id_and_name(id, name):
        if id == "newgroup":
            releaser = Releaser(name=name, is_group=True, updated_at=datetime.datetime.now())
            releaser.save()
            return releaser.primary_nick
        elif id == "newscener":
            releaser = Releaser(name=name, is_group=False, updated_at=datetime.datetime.now())
            releaser.save()
            return releaser.primary_nick
        else:
            return Nick.objects.get(id=id)

    def get_nick_variant_list(self):
        if self._has_written_nick_variant_list:
            return self._nick_variant_list
        else:
            if self.pk is None:
                return ""
            else:
                variant_names = [
                    variant.name for variant in self.variants.exclude(name__in=[self.name, self.abbreviation])
                ]
                return ", ".join(variant_names)

    def set_nick_variant_list(self, new_list):
        self._nick_variant_list = new_list
        self._has_written_nick_variant_list = True

    nick_variant_list = property(get_nick_variant_list, set_nick_variant_list)

    @property
    def nick_variant_and_abbreviation_list(self):
        if self.has_prefetched("variants"):
            variant_names = [variant.name for variant in self.variants.all() if variant.name != self.name]
        else:
            variant_names = [variant.name for variant in self.variants.exclude(name=self.name)]
        return ", ".join(variant_names)

    def save(self, *args, **kwargs):
        # update releaser's name if it matches this nick's previous name
        if self.id is not None:
            old_name = Nick.objects.get(id=self.id).name
            super().save(*args, **kwargs)  # Call the original save() method
            if (old_name == self.releaser.name) and (old_name != self.name):
                self.releaser.name = self.name
                self.releaser.save()
        else:
            super().save(*args, **kwargs)  # Call the original save() method
            if not self._has_written_nick_variant_list:
                # force writing a nick variant list containing just the primary nick (and abbreviation if specified)
                self._has_written_nick_variant_list = True
                self._nick_variant_list = ""

        if self._has_written_nick_variant_list:
            # update the nick variant list
            old_variant_names = [variant.name for variant in self.variants.all()]
            new_variant_names = re.split(r"\s*\,\s*", self._nick_variant_list)
            new_variant_names.append(self.name)
            if self.abbreviation and self.abbreviation.lower() != self.name.lower():
                new_variant_names.append(self.abbreviation)

            for variant in self.variants.all():
                if variant.name not in new_variant_names:
                    variant.delete()
            for variant_name in new_variant_names:
                if variant_name and variant_name not in old_variant_names:
                    variant = NickVariant(nick=self, name=variant_name)
                    variant.save()

            self._has_written_nick_variant_list = False

    def name_with_affiliations(self):
        groups = self.releaser.current_groups(prefetch_nicks=True)

        if groups:
            if sum([len(group.name) for group in groups]) >= 20:
                # abbreviate where possible
                group_names = [(group.abbreviation or group.name) for group in groups]
            else:
                # use full group names - not too long
                group_names = [group.name for group in groups]
            return "%s / %s" % (self.name, " ^ ".join(group_names))
        else:
            return self.name

    # Determine whether or not this nick is referenced in any external records (credits, authorships etc)
    def is_referenced(self):
        return self.credits.count() or self.productions.count() or self.member_productions.count()

    # Reassign credits/productions that reference this nick to use the releaser's primary nick instead,
    # then delete this nick
    def reassign_references_and_delete(self):
        primary_nick = self.releaser.primary_nick
        if primary_nick == self:
            raise Exception("attempted to delete a releaser's primary nick through reassign_references_and_delete!")

        from django.db import connection

        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute("UPDATE productions_credit SET nick_id = %s WHERE nick_id = %s", [primary_nick.id, self.id])
            cursor.execute(
                "UPDATE productions_production_author_nicks SET nick_id = %s WHERE nick_id = %s",
                [primary_nick.id, self.id],
            )
            cursor.execute(
                "UPDATE productions_production_author_affiliation_nicks SET nick_id = %s WHERE nick_id = %s",
                [primary_nick.id, self.id],
            )

        self.delete()

    def is_primary_nick(self):
        return self.releaser.name == self.name

    class Meta:
        unique_together = ("releaser", "name")
        ordering = ["name"]


class NickVariant(models.Model):
    nick = models.ForeignKey(Nick, related_name="variants", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    search_title = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        # populate search_title from name
        if self.name:
            self.search_title = generate_search_title(self.name)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @staticmethod
    def autocomplete(initial_query, **kwargs):
        # look for possible autocompletions; choose the top-ranked one and use that as the query

        # match names which are an EXACT match for the stripped name, or a prefix of the non-stripped
        # name. e.g.: "Andromeda " will match both "Andromeda Software Development" and "Andromeda",
        # but "Far " will only match "Far", not "Farbrausch"

        exact_matches = NickVariant.autocompletion_search(initial_query.strip(), exact=True, limit=1, **kwargs)
        if exact_matches:
            return ""  # if an exact match exists, there's nothing to autocomplete

        # look for prefixes instead
        lstripped_query = initial_query.lstrip()
        autocompletions = NickVariant.autocompletion_search(lstripped_query, limit=1, **kwargs)
        try:
            result = autocompletions[0].name
            # return just the suffix to add; the caller will append this to the original query,
            # thus preserving capitalisation in exactly the way that iTunes doesn't.
            # (Ha, I rule.)
            return result[len(lstripped_query) :]
        except IndexError:  # no autocompletions available
            return ""

    @staticmethod
    def autocompletion_search(query, **kwargs):
        limit = kwargs.get("limit")
        exact = kwargs.get("exact", False)
        groups_only = kwargs.get("groups_only", False)
        sceners_only = kwargs.get("sceners_only", False)

        group_ids = kwargs.get("group_ids", [])
        group_names = [name.lower() for name in kwargs.get("group_names", [])]
        member_names = [name.lower() for name in kwargs.get("member_names", [])]

        if query:
            if exact:
                nick_variants = NickVariant.objects.filter(name__iexact=query)
            else:
                nick_variants = NickVariant.objects.filter(name__istartswith=query)

            if groups_only:
                nick_variants = nick_variants.filter(nick__releaser__is_group=True)
            elif sceners_only:
                nick_variants = nick_variants.filter(nick__releaser__is_group=False)
            else:
                # nasty hack to ensure that we're joining on releaser, for the 'group_names' subquery
                nick_variants = nick_variants.filter(nick__releaser__is_group__in=[True, False])

            if group_ids:
                # Add a 'score' field that prioritises releasers that are members of any of the specified groups
                select = SortedDict(
                    [
                        (
                            "score",
                            """
                        SELECT COUNT(*) FROM demoscene_membership
                        WHERE demoscene_membership.member_id = demoscene_releaser.id
                        AND demoscene_membership.group_id = ANY(%s)
                    """,
                        ),
                    ]
                )
                select_params = [list(group_ids)]
            elif group_names:
                # Add a 'score' field that prioritises releasers that are members of a group with one of the given names
                select = SortedDict(
                    [
                        (
                            "score",
                            """
                        SELECT COUNT(*) FROM demoscene_membership
                        INNER JOIN demoscene_releaser AS demogroup ON (demoscene_membership.group_id = demogroup.id)
                        INNER JOIN demoscene_nick AS group_nick ON (demogroup.id = group_nick.releaser_id)
                        INNER JOIN demoscene_nickvariant AS group_nickvariant ON (
                            group_nick.id = group_nickvariant.nick_id
                        )
                        WHERE demoscene_membership.member_id = demoscene_releaser.id
                        AND LOWER(group_nickvariant.name) = ANY(%s)
                    """,
                        ),
                    ]
                )
                select_params = [list(group_names)]
            elif member_names:
                # Add a 'score' field that prioritises groups that have members with one of the given names
                select = SortedDict(
                    [
                        (
                            "score",
                            """
                        SELECT COUNT(*) FROM demoscene_membership
                        INNER JOIN demoscene_releaser AS member ON (demoscene_membership.member_id = member.id)
                        INNER JOIN demoscene_nick AS member_nick ON (member.id = member_nick.releaser_id)
                        INNER JOIN demoscene_nickvariant AS member_nickvariant ON (
                            member_nick.id = member_nickvariant.nick_id
                        )
                        WHERE demoscene_membership.group_id = demoscene_releaser.id
                        AND LOWER(member_nickvariant.name) = ANY (%s)
                    """,
                        ),
                    ]
                )
                select_params = [list(member_names)]
            else:
                select = SortedDict(
                    [
                        ("score", "0"),
                    ]
                )
                select_params = []

            # Add an 'is_exact_match' column to the results - true if the query matches the result exactly
            select["is_exact_match"] = """
                CASE WHEN LOWER(demoscene_nickvariant.name) = LOWER(%s) THEN 1 ELSE 0 END
            """
            select_params.append(query)

            # Add an 'is_primary_nickvariant' column to the results -
            # true if the matched nick variant is the nick's primary one
            select["is_primary_nickvariant"] = """
                CASE WHEN demoscene_nick.name = demoscene_nickvariant.name THEN 1 ELSE 0 END
            """

            nick_variants = nick_variants.extra(
                select=select,
                select_params=select_params,
                order_by=("-score", "-is_exact_match", "-is_primary_nickvariant", "name"),
            )

            if limit:
                nick_variants = nick_variants[:limit]

            nick_variants = nick_variants.select_related("nick", "nick__releaser")
            nick_variants = nick_variants.only(
                "id",
                "name",
                "nick__id",
                "nick__name",
                "nick__differentiator",
                "nick__releaser__is_group",
                "nick__releaser__country_code",
            )
        else:
            nick_variants = NickVariant.objects.none()

        return nick_variants

    class Meta:
        ordering = ["name"]


class Membership(models.Model):
    member = models.ForeignKey(Releaser, related_name="group_memberships", on_delete=models.CASCADE)
    group = models.ForeignKey(
        Releaser, limit_choices_to={"is_group": True}, related_name="member_memberships", on_delete=models.CASCADE
    )
    is_current = models.BooleanField(default=True)
    data_source = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return "%s / %s" % (self.member.name, self.group.name)


class AccountProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    demozoo0_id = models.IntegerField(null=True, blank=True, verbose_name="Demozoo v0 ID")

    def __str__(self):
        try:
            return str(self.user)
        except User.DoesNotExist:
            return "(AccountProfile)"

    class Meta:
        ordering = ["user__username"]


class ExternalLink(models.Model):
    link_class = models.CharField(max_length=100)
    parameter = models.CharField(max_length=4096)

    def _get_url(self):
        if self.link:
            return str(self.link)
        else:
            return None

    def _set_url(self, urlstring):
        if urlstring:
            self.link = groklinks.grok_link_by_types(urlstring.strip(), self.link_types)
            if self.link:
                self.link_class = self.link.__class__.__name__
                self.parameter = self.link.param
            else:  # pragma: no cover
                self.link_class = None
                self.parameter = None
        else:
            self.link_class = None
            self.parameter = None

    url = property(_get_url, _set_url)

    def html_link(self):
        return self.link.as_html(self.subject)

    def html_icon_link(self):
        return self.link.as_icon_link(self.subject)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.link_class:
            self.link = groklinks.__dict__[self.link_class](self.parameter)
        else:
            self.link = None

    @property
    def sort_key(self):
        return "0000" if self.link_class == "BaseUrl" else self.link_class

    class Meta:
        abstract = True
        ordering = ["link_class"]


class ReleaserExternalLink(ExternalLink):
    releaser = models.ForeignKey(Releaser, related_name="external_links", on_delete=models.CASCADE)
    link_types = groklinks.RELEASER_LINK_TYPES
    source = models.CharField(
        max_length=32,
        blank=True,
        editable=False,
        help_text="Identifier to indicate where this link came from - e.g. manual (entered via form), match, auto",
    )

    @property
    def subject(self):
        return self.releaser.name

    class Meta:
        unique_together = (("link_class", "parameter", "releaser"),)
        ordering = ["link_class"]


class Edit(models.Model):
    action_type = models.CharField(max_length=100)

    focus_content_type = models.ForeignKey(ContentType, related_name="edits", on_delete=models.CASCADE)
    focus_object_id = models.PositiveIntegerField()
    focus = GenericForeignKey("focus_content_type", "focus_object_id")

    focus2_content_type = models.ForeignKey(
        ContentType, null=True, blank=True, related_name="edits_as_focus2", on_delete=models.CASCADE
    )
    focus2_object_id = models.PositiveIntegerField(null=True, blank=True)
    focus2 = GenericForeignKey("focus2_content_type", "focus2_object_id")

    description = models.TextField()
    user = models.ForeignKey(User, related_name="edits", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    admin_only = models.BooleanField(default=False)

    @staticmethod
    def for_model(model, is_admin=False):
        model_type = ContentType.objects.get_for_model(model)
        edits = Edit.objects.all()
        if not is_admin:
            edits = edits.filter(admin_only=False)
        edits = (
            edits.extra(
                where=[
                    """(
            (focus_content_type_id = %s AND focus_object_id = %s)
            OR (focus2_content_type_id = %s AND focus2_object_id = %s)
        )"""
                ],
                params=[model_type.id, model.id, model_type.id, model.id],
            )
            .order_by("-timestamp")
            .select_related("user")
        )
        return edits

    class Meta:
        indexes = [
            models.Index(fields=["focus_content_type", "focus_object_id"]),
            models.Index(fields=["focus2_content_type", "focus2_object_id"]),
        ]


class CaptchaQuestion(models.Model):
    question = models.TextField(
        help_text=(
            "HTML is allowed. Keep questions factual and simple - "
            "remember that our potential users are not always followers of mainstream demoparty culture"
        )
    )
    answer = models.CharField(
        max_length=255,
        help_text="Answers are not case sensitive (the correct answer will be accepted regardless of capitalisation)",
    )

    def __str__(self):
        return self.question


class TagDescription(models.Model):
    tag = models.OneToOneField("taggit.Tag", primary_key=True, related_name="description", on_delete=models.CASCADE)
    description = models.TextField(
        help_text=(
            "HTML is allowed. Keep this to a couple of sentences at most - "
            "it's used in tooltips as well as the tag listing page"
        )
    )

    def __str__(self):
        return self.tag.name


class BlacklistedTag(models.Model):
    tag = models.CharField(max_length=255, help_text="The tag to be blacklisted")
    replacement = models.CharField(
        max_length=255, blank=True, help_text="What to replace the tag with (leave blank to delete it completely)"
    )
    message = models.TextField(
        blank=True, help_text="Message to show to the user when they try to use the tag (optional)"
    )

    def __str__(self):
        return self.tag


class SceneID(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sceneid = models.IntegerField()


class TextFile(models.Model):
    filename = models.CharField(max_length=255, blank=True)
    filesize = models.IntegerField()
    sha1 = models.CharField(max_length=40)
    encoding = models.CharField(blank=True, null=True, max_length=32)

    def save(self, *args, **kwargs):
        self.file.open()
        self.file.seek(0)
        data = self.file.read()
        self.file.seek(0)

        self.filesize = len(data)
        self.sha1 = hashlib.sha1(data).hexdigest()

        if not self.filename:
            self.filename = self.file.name

        if not self.encoding:
            decode = self.guess_encoding(data)
            if decode:
                self.encoding = decode[0]
        super().save(*args, **kwargs)
        self.file.close()

    @staticmethod
    def guess_encoding(data, fuzzy=False):
        """
        Make a best guess at what character encoding this data is in.
        Returns a tuple of (encoding, decoded_data).
        If fuzzy=False, we return None if the encoding is uncertain;
        if fuzzy=True, we make a wild guess.
        """
        # Try to decode the data using several candidate encodings, least permissive first.
        # Accept the first one that doesn't break.
        if fuzzy:
            candidate_encodings = ["ascii", "utf-8", "cp437", "windows-1252", "iso-8859-1"]
        else:
            candidate_encodings = ["ascii", "utf-8"]

        for encoding in candidate_encodings:
            try:
                return (encoding, data.decode(encoding))
            except UnicodeDecodeError:
                pass

    @cached_property
    def data(self):
        self.file.open()
        self.file.seek(0)
        data = self.file.read()
        self.file.close()
        return data

    def is_ansi(self):
        """whether this file contains ANSI escape codes"""
        return b"\x1b[" in self.data

    @property
    def text(self):
        if self.encoding:
            return self.data.decode(self.encoding)
        else:
            encoding, output = self.guess_encoding(self.data, fuzzy=True)
            return output

    def as_renderable(self):
        """
        Return the text in a form that can be included into a template; either a plain string
        (which the template engine will escape) or a SafeString containing HTML
        """
        if self.is_ansi():
            ansi = ANSIDecoder(StringIO(self.text))
            return mark_safe(ansi.as_html())
        else:
            return self.text

    class Meta:
        abstract = True
