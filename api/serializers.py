from rest_framework import serializers

from demoscene.models import Releaser, Nick, Membership, ReleaserExternalLink
from productions.models import Production, ProductionLink


class NickSerializer(serializers.ModelSerializer):
	variants = serializers.StringRelatedField(many=True)
	class Meta:
		model = Nick
		fields = ['name', 'abbreviation', 'is_primary_nick', 'variants']

class NickSummarySerializer(serializers.ModelSerializer):
	class Meta:
		model = Nick
		fields = ['name', 'abbreviation']

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

class ReleaserExternalLinkSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReleaserExternalLink
		fields = ['link_class', 'url']

class ReleaserSerializer(serializers.HyperlinkedModelSerializer):
	nicks = NickSerializer(many=True, read_only=True)
	member_of = serializers.SerializerMethodField('get_group_memberships')
	members = serializers.SerializerMethodField()
	subgroups = serializers.SerializerMethodField()
	external_links = ReleaserExternalLinkSerializer(many=True, read_only=True)

	def get_group_memberships(self, releaser):
		memberships = releaser.group_memberships.select_related('group')
		return GroupMembershipSerializer(instance=memberships, many=True, context=self.context).data

	def get_members(self, releaser):
		member_memberships = releaser.member_memberships.filter(member__is_group=False).select_related('member')
		return MemberMembershipSerializer(instance=member_memberships, many=True, context=self.context).data

	def get_subgroups(self, releaser):
		member_memberships = releaser.member_memberships.filter(member__is_group=True).select_related('member')
		return MemberMembershipSerializer(instance=member_memberships, many=True, context=self.context).data

	class Meta:
		model = Releaser
		fields = ['url', 'id', 'name', 'is_group', 'nicks', 'member_of', 'members', 'subgroups', 'external_links']


class ProductionExternalLinkSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProductionLink
		fields = ['link_class', 'url']

class ProductionSerializer(serializers.HyperlinkedModelSerializer):
	author_nicks = NickSummarySerializer(many=True, read_only=True)
	links = ProductionExternalLinkSerializer(many=True, read_only=True)

	class Meta:
		model = Production
		fields = ['url', 'id', 'title', 'author_nicks', 'links']
