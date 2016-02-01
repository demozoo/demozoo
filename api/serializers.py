from django.conf import settings

from rest_framework import serializers

from demoscene.models import Releaser, Nick, Membership, ReleaserExternalLink
from platforms.models import Platform
from productions.models import Production, ProductionLink, Credit, ProductionType, Screenshot


class NickSerializer(serializers.ModelSerializer):
	variants = serializers.StringRelatedField(many=True)

	class Meta:
		model = Nick
		fields = ['name', 'abbreviation', 'is_primary_nick', 'variants']


class ReleaserListingSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Releaser
		fields = ['url', 'id', 'name', 'is_group']


class ReleaserSummarySerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Releaser
		fields = ['url', 'id', 'name']


class GroupMembershipSerializer(serializers.ModelSerializer):
	group = ReleaserSummarySerializer(read_only=True)

	class Meta:
		model = Membership
		fields = ['group', 'is_current']


class MemberMembershipSerializer(serializers.ModelSerializer):
	member = ReleaserSummarySerializer(read_only=True)

	class Meta:
		model = Membership
		fields = ['member', 'is_current']


class SubgroupMembershipSerializer(serializers.ModelSerializer):
	subgroup = serializers.SerializerMethodField(read_only=True)

	def get_subgroup(self, membership):
		return ReleaserSummarySerializer(instance=membership.member, context=self.context).data

	class Meta:
		model = Membership
		fields = ['subgroup', 'is_current']


class ReleaserExternalLinkSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReleaserExternalLink
		fields = ['link_class', 'url']


class ReleaserSerializer(serializers.HyperlinkedModelSerializer):
	demozoo_url = serializers.SerializerMethodField(read_only=True)
	nicks = NickSerializer(many=True, read_only=True)
	member_of = serializers.SerializerMethodField('get_group_memberships', read_only=True)
	members = serializers.SerializerMethodField(read_only=True)
	subgroups = serializers.SerializerMethodField(read_only=True)
	external_links = ReleaserExternalLinkSerializer(many=True, read_only=True)

	def get_demozoo_url(self, releaser):
		return settings.BASE_URL + releaser.get_absolute_url()

	def get_group_memberships(self, releaser):
		memberships = releaser.group_memberships.select_related('group')
		return GroupMembershipSerializer(instance=memberships, many=True, context=self.context).data

	def get_members(self, releaser):
		member_memberships = releaser.member_memberships.filter(member__is_group=False).select_related('member')
		return MemberMembershipSerializer(instance=member_memberships, many=True, context=self.context).data

	def get_subgroups(self, releaser):
		member_memberships = releaser.member_memberships.filter(member__is_group=True).select_related('member')
		return SubgroupMembershipSerializer(instance=member_memberships, many=True, context=self.context).data

	class Meta:
		model = Releaser
		fields = ['url', 'demozoo_url', 'id', 'name', 'is_group', 'nicks', 'member_of', 'members', 'subgroups', 'external_links']


class PlatformSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Platform
		fields = ['url', 'id', 'name']


class ProductionTypeSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = ProductionType
		fields = ['url', 'id', 'name', 'supertype']


class ProductionTypeSummarySerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = ProductionType
		fields = ['url', 'id', 'name']


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Releaser
		fields = ['url', 'id', 'name', 'is_group']


class AuthorNickSerializer(serializers.ModelSerializer):
	releaser = AuthorSerializer(read_only=True)

	class Meta:
		model = Nick
		fields = ['name', 'abbreviation', 'releaser']


class ProductionExternalLinkSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProductionLink
		fields = ['link_class', 'url']


class ProductionCreditSerializer(serializers.ModelSerializer):
	nick = AuthorNickSerializer(read_only=True)

	class Meta:
		model = Credit
		fields = ['nick', 'category', 'role']


class ScreenshotSerializer(serializers.ModelSerializer):
	class Meta:
		model = Screenshot
		fields = [
			'original_url', 'original_width', 'original_height',
			'standard_url', 'standard_width', 'standard_height',
			'thumbnail_url', 'thumbnail_width', 'thumbnail_height',
		]


class ProductionListingSerializer(serializers.HyperlinkedModelSerializer):
	author_nicks = AuthorNickSerializer(many=True, read_only=True)
	author_affiliation_nicks = AuthorNickSerializer(many=True, read_only=True)
	platforms = PlatformSerializer(many=True, read_only=True)
	types = ProductionTypeSummarySerializer(many=True, read_only=True)

	class Meta:
		model = Production
		fields = ['url', 'id', 'title', 'author_nicks', 'author_affiliation_nicks', 'supertype', 'platforms', 'types']


class ProductionSerializer(serializers.HyperlinkedModelSerializer):
	demozoo_url = serializers.SerializerMethodField(read_only=True)
	author_nicks = AuthorNickSerializer(many=True, read_only=True)
	author_affiliation_nicks = AuthorNickSerializer(many=True, read_only=True)
	platforms = PlatformSerializer(many=True, read_only=True)
	types = ProductionTypeSerializer(many=True, read_only=True)
	credits = ProductionCreditSerializer(many=True, read_only=True)
	download_links = ProductionExternalLinkSerializer(many=True, read_only=True)
	external_links = ProductionExternalLinkSerializer(many=True, read_only=True)
	screenshots = ScreenshotSerializer(many=True, read_only=True)

	def get_demozoo_url(self, production):
		return settings.BASE_URL + production.get_absolute_url()

	class Meta:
		model = Production
		fields = [
			'url', 'demozoo_url', 'id', 'title', 'author_nicks', 'author_affiliation_nicks', 'supertype', 'platforms', 'types',
			'credits', 'download_links', 'external_links', 'screenshots']
