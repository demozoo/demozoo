import responses
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from requests.exceptions import HTTPError

from awards.models import Event, Juror
from demoscene.models import SceneID


class TestFetchJurors(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.juror_feed_url = "http://example.com/meteoriks-jurors.txt"
        meteoriks.save()

        self.testuser = User.objects.create_user(username="testuser", password="12345")
        self.truck = User.objects.create_user(username="truck", password="56789")
        SceneID.objects.create(user=self.testuser, sceneid=4242)
        SceneID.objects.create(user=self.truck, sceneid=666)
        Juror.objects.create(user=self.truck, event=meteoriks)

    @responses.activate
    def test_fetch_fail(self):
        exception = HTTPError("Something went wrong")
        responses.add(responses.GET, "http://example.com/meteoriks-jurors.txt", body=exception)
        with captured_stdout():
            call_command("fetch_award_jurors")

        self.assertEqual(Juror.objects.filter(user=self.testuser).count(), 0)

    @responses.activate
    def test_fetch(self):
        responses.add(responses.GET, "http://example.com/meteoriks-jurors.txt", body="4242  # testuser\n666  # truck\n")
        call_command("fetch_award_jurors")

        self.assertEqual(Juror.objects.filter(user=self.testuser).count(), 1)
        self.assertEqual(Juror.objects.filter(user=self.truck).count(), 1)
