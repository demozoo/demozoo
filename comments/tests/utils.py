import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from common.utils.fuzzy_date import FuzzyDate
from comments.models import Comment
from parties.models import Party, PartySeries
from productions.models import Production


class CommentTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='password')
        self.admin.is_staff = True
        self.admin.save()

        self.user = User.objects.create_user(username='bob the commenter', password='password')
        self.production = Production.objects.create(
            title="Second Reality",
            supertype='production',  # FIXME: can't this be set in save() on first create?
        )
        self.uncommented_production = Production.objects.create(
            title="BITS 99",
            supertype='production',
        )
        self.production_comment = Comment.objects.create(
            user=self.user,
            commentable=self.production,
            body="He is not an atomic playboy.",
            created_at=datetime.datetime(2014, 1, 1)
        )
        self.second_production_comment = Comment.objects.create(
            user=self.user,
            commentable=self.production,
            body="On second thoughts, maybe he is.",
            created_at=datetime.datetime(2014, 1, 2)
        )
        self.party_series = PartySeries.objects.create(name="InerciaDemoparty")
        self.party = Party.objects.create(
            party_series=self.party_series,
            start_date=FuzzyDate.parse('2005'),
            end_date=FuzzyDate.parse('2005'),
            name="InerciaDemoparty 2005"
        )
        self.party_comment = Comment.objects.create(
            user=self.user,
            commentable=self.party,
            body="I forgot to come."
        )

    def login(self):
        self.client.login(username='bob the commenter', password='password')

    def login_as_admin(self):
        self.client.login(username='admin', password='password')
