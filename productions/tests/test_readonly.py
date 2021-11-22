import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from productions.models import Production


@unittest.skipIf(settings.SITE_IS_WRITEABLE, "not running in read only mode")
class TestEditCoreDetails(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get_production(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get('/productions/%d/edit_core_details/' % pondlife.id)
        self.assertRedirects(response, '/')

    def test_get_production_ajax(self):
        pondlife = Production.objects.get(title='Pondlife')
        response = self.client.get(
            '/productions/%d/edit_core_details/' % pondlife.id,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertContains(response, "The website is in read-only mode at the moment.")
