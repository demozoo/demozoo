from django.conf import settings
from rest_framework import serializers

from bbs.models import BBS, Affiliation, Operator
from demoscene.models import Membership, Nick, Releaser, ReleaserExternalLink
from parties.models import Competition, CompetitionPlacing, Party, PartyExternalLink, PartySeries
from platforms.models import Platform
from productions.models import Credit, Production, ProductionLink, ProductionType, Screenshot


class OutputFieldsMixin:
    """
    When mixed in to a serializer class, allows passing a `fields` kwarg to the constructor
    to specify a list of field names to include in the output record
    """

    def __init__(self, *args, **kwargs):
        self._output_fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

    def get_fields(self):
        fields = super().get_fields()
        if self._output_fields is not None:
            fields = {k: v for k, v in fields.items() if k in self._output_fields}
        return fields


# Summary serialisers (for inline listings in other records)

PRODUCTION_LISTING_FIELDS = [
    "url",
    "demozoo_url",
    "id",
    "title",
    "author_nicks",
    "author_affiliation_nicks",
    "release_date",
    "supertype",
    "platforms",
    "types",
    "tags",
]

PARTY_SERIES_LISTING_FIELDS = ["url", "demozoo_url", "id", "name", "website"]

PARTY_LISTING_FIELDS = [
    "url",
    "demozoo_url",
    "id",
    "name",
    "tagline",
    "start_date",
    "end_date",
    "location",
    "is_online",
    "country_code",
    "latitude",
    "longitude",
    "website",
]


class ReleaserSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Releaser
        fields = ["url", "id", "name"]


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Releaser
        fields = ["url", "id", "name", "is_group"]


class AuthorNickSerializer(serializers.ModelSerializer):
    releaser = AuthorSerializer(read_only=True)

    class Meta:
        model = Nick
        fields = ["name", "abbreviation", "releaser"]


class PartySeriesSummarySerializer(serializers.HyperlinkedModelSerializer):
    demozoo_url = serializers.SerializerMethodField(read_only=True)

    def get_demozoo_url(self, party_series):
        return settings.BASE_URL + party_series.get_absolute_url()

    class Meta:
        model = PartySeries
        fields = PARTY_SERIES_LISTING_FIELDS


class PartySummarySerializer(serializers.HyperlinkedModelSerializer):
    demozoo_url = serializers.SerializerMethodField(read_only=True)
    start_date = serializers.SerializerMethodField(read_only=True)
    end_date = serializers.SerializerMethodField(read_only=True)

    def get_demozoo_url(self, party):
        return settings.BASE_URL + party.get_absolute_url()

    def get_start_date(self, party):
        start_date = party.start_date
        return start_date and start_date.numeric_format()

    def get_end_date(self, party):
        end_date = party.end_date
        return end_date and end_date.numeric_format()

    class Meta:
        model = Party
        fields = PARTY_LISTING_FIELDS


# Listing serialisers


class ProductionTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProductionType
        fields = ["url", "id", "name", "supertype"]


class PlatformSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Platform
        fields = ["url", "id", "name"]


# Detail serialisers


class ReleaserSerializer(OutputFieldsMixin, serializers.HyperlinkedModelSerializer):
    class NickSerializer(serializers.ModelSerializer):
        variants = serializers.StringRelatedField(many=True)

        class Meta:
            model = Nick
            fields = ["name", "abbreviation", "is_primary_nick", "variants"]

    class GroupMembershipSerializer(serializers.ModelSerializer):
        group = ReleaserSummarySerializer(read_only=True)

        class Meta:
            model = Membership
            fields = ["group", "is_current"]

    class MemberMembershipSerializer(serializers.ModelSerializer):
        member = ReleaserSummarySerializer(read_only=True)

        class Meta:
            model = Membership
            fields = ["member", "is_current"]

    class SubgroupMembershipSerializer(serializers.ModelSerializer):
        subgroup = serializers.SerializerMethodField(read_only=True)

        def get_subgroup(self, membership):
            return ReleaserSummarySerializer(instance=membership.member, context=self.context).data

        class Meta:
            model = Membership
            fields = ["subgroup", "is_current"]

    class ReleaserExternalLinkSerializer(serializers.ModelSerializer):
        class Meta:
            model = ReleaserExternalLink
            fields = ["link_class", "url"]

    demozoo_url = serializers.SerializerMethodField(read_only=True)
    nicks = NickSerializer(many=True, read_only=True)
    member_of = serializers.SerializerMethodField("get_group_memberships", read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    subgroups = serializers.SerializerMethodField(read_only=True)
    external_links = ReleaserExternalLinkSerializer(many=True, read_only=True, source="active_external_links")

    def get_demozoo_url(self, releaser):
        return settings.BASE_URL + releaser.get_absolute_url()

    def get_group_memberships(self, releaser):
        memberships = releaser.group_memberships.select_related("group")
        return ReleaserSerializer.GroupMembershipSerializer(instance=memberships, many=True, context=self.context).data

    def get_members(self, releaser):
        member_memberships = releaser.member_memberships.filter(member__is_group=False).select_related("member")
        return ReleaserSerializer.MemberMembershipSerializer(
            instance=member_memberships, many=True, context=self.context
        ).data

    def get_subgroups(self, releaser):
        member_memberships = releaser.member_memberships.filter(member__is_group=True).select_related("member")
        return ReleaserSerializer.SubgroupMembershipSerializer(
            instance=member_memberships, many=True, context=self.context
        ).data

    class Meta:
        model = Releaser
        fields = [
            "url",
            "demozoo_url",
            "id",
            "name",
            "is_group",
            "nicks",
            "member_of",
            "members",
            "subgroups",
            "external_links",
        ]


class ProductionSerializer(OutputFieldsMixin, serializers.HyperlinkedModelSerializer):
    class ProductionExternalLinkSerializer(serializers.ModelSerializer):
        class Meta:
            model = ProductionLink
            fields = ["link_class", "url"]

    class ProductionCreditSerializer(serializers.ModelSerializer):
        nick = AuthorNickSerializer(read_only=True)

        class Meta:
            model = Credit
            fields = ["nick", "category", "role"]

    class ProductionCompetitionPlacingSerializer(serializers.ModelSerializer):
        class CompetitionPlacingCompetitionSerializer(serializers.ModelSerializer):
            party = PartySummarySerializer(read_only=True)

            class Meta:
                model = Competition
                fields = ["id", "name", "party"]

        competition = CompetitionPlacingCompetitionSerializer(read_only=True)

        class Meta:
            model = CompetitionPlacing
            fields = ["position", "ranking", "score", "competition"]

    class ScreenshotSerializer(serializers.ModelSerializer):
        class Meta:
            model = Screenshot
            fields = [
                "original_url",
                "original_width",
                "original_height",
                "standard_url",
                "standard_width",
                "standard_height",
                "thumbnail_url",
                "thumbnail_width",
                "thumbnail_height",
            ]

    demozoo_url = serializers.SerializerMethodField(read_only=True)
    author_nicks = AuthorNickSerializer(many=True, read_only=True)
    author_affiliation_nicks = AuthorNickSerializer(many=True, read_only=True)
    release_date = serializers.SerializerMethodField(read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    types = ProductionTypeSerializer(many=True, read_only=True)
    credits = ProductionCreditSerializer(many=True, read_only=True)
    download_links = ProductionExternalLinkSerializer(many=True, read_only=True)
    external_links = ProductionExternalLinkSerializer(many=True, read_only=True)
    release_parties = PartySummarySerializer(many=True, read_only=True)
    competition_placings = ProductionCompetitionPlacingSerializer(many=True, read_only=True)
    invitation_parties = PartySummarySerializer(many=True, read_only=True)
    screenshots = ScreenshotSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)

    def get_demozoo_url(self, production):
        return settings.BASE_URL + production.get_absolute_url()

    def get_release_date(self, production):
        release_date = production.release_date
        return release_date and release_date.numeric_format()

    def get_tags(self, bbs):
        return [tag.name for tag in bbs.tags.all()]

    class Meta:
        model = Production
        fields = [
            "url",
            "demozoo_url",
            "id",
            "title",
            "author_nicks",
            "author_affiliation_nicks",
            "release_date",
            "supertype",
            "platforms",
            "types",
            "credits",
            "download_links",
            "external_links",
            "release_parties",
            "competition_placings",
            "invitation_parties",
            "screenshots",
            "tags",
        ]


class PartySerializer(OutputFieldsMixin, PartySummarySerializer):
    class CompetitionSerializer(serializers.ModelSerializer):
        class CompetitionPlacingSerializer(serializers.ModelSerializer):
            production = ProductionSerializer(read_only=True, fields=PRODUCTION_LISTING_FIELDS)

            class Meta:
                model = CompetitionPlacing
                fields = ["position", "ranking", "score", "production"]

        demozoo_url = serializers.SerializerMethodField(read_only=True)
        shown_date = serializers.SerializerMethodField(read_only=True)
        platform = PlatformSerializer(read_only=True)
        production_type = ProductionTypeSerializer(read_only=True)
        results = CompetitionPlacingSerializer(many=True, read_only=True)

        def get_demozoo_url(self, competition):
            return settings.BASE_URL + competition.get_absolute_url()

        def get_shown_date(self, competition):
            shown_date = competition.shown_date
            return shown_date and shown_date.numeric_format()

        class Meta:
            model = Competition
            fields = ["id", "demozoo_url", "name", "shown_date", "platform", "production_type", "results"]

    class PartyExternalLinkSerializer(serializers.ModelSerializer):
        class Meta:
            model = PartyExternalLink
            fields = ["link_class", "url"]

    party_series = PartySeriesSummarySerializer(read_only=True)
    invitations = ProductionSerializer(many=True, read_only=True, fields=PRODUCTION_LISTING_FIELDS)
    releases = ProductionSerializer(many=True, read_only=True, fields=PRODUCTION_LISTING_FIELDS)
    competitions = serializers.SerializerMethodField(read_only=True)
    external_links = PartyExternalLinkSerializer(many=True, read_only=True, source="active_external_links")

    def get_competitions(self, party):
        competitions = party.get_competitions_with_prefetched_results(include_tags=True)
        return PartySerializer.CompetitionSerializer(instance=competitions, many=True, context=self.context).data

    class Meta(PartySummarySerializer.Meta):
        fields = [
            "url",
            "demozoo_url",
            "id",
            "name",
            "tagline",
            "party_series",
            "start_date",
            "end_date",
            "location",
            "is_online",
            "country_code",
            "latitude",
            "longitude",
            "website",
            "invitations",
            "releases",
            "competitions",
            "external_links",
        ]


class PartySeriesSerializer(OutputFieldsMixin, PartySeriesSummarySerializer):
    parties = PartySummarySerializer(many=True, read_only=True)

    class Meta(PartySeriesSummarySerializer.Meta):
        fields = ["url", "demozoo_url", "id", "name", "website", "parties"]


class BBSSerializer(OutputFieldsMixin, serializers.HyperlinkedModelSerializer):
    class BBSOperatorSerializer(serializers.ModelSerializer):
        releaser = ReleaserSummarySerializer(read_only=True)

        class Meta:
            model = Operator
            fields = ["releaser", "role", "is_current"]

    class BBSAffiliationSerializer(serializers.ModelSerializer):
        group = ReleaserSummarySerializer(read_only=True)

        class Meta:
            model = Affiliation
            fields = ["group", "role"]

    demozoo_url = serializers.SerializerMethodField(read_only=True)
    bbstros = ProductionSerializer(many=True, read_only=True, fields=PRODUCTION_LISTING_FIELDS)
    staff = serializers.SerializerMethodField(read_only=True)
    affiliations = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)

    def get_demozoo_url(self, bbs):
        return settings.BASE_URL + bbs.get_absolute_url()

    def get_staff(self, bbs):
        operators = bbs.staff.select_related("releaser")
        return BBSSerializer.BBSOperatorSerializer(instance=operators, many=True, context=self.context).data

    def get_affiliations(self, bbs):
        affiliations = bbs.affiliations.select_related("group")
        return BBSSerializer.BBSAffiliationSerializer(instance=affiliations, many=True, context=self.context).data

    def get_tags(self, bbs):
        return [tag.name for tag in bbs.tags.all()]

    class Meta:
        model = BBS
        fields = [
            "url",
            "demozoo_url",
            "id",
            "name",
            "location",
            "country_code",
            "latitude",
            "longitude",
            "bbstros",
            "staff",
            "affiliations",
            "tags",
        ]
