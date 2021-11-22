from django.test import TestCase

from platforms.models import Platform


class TestShowIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/platforms/')
        self.assertEqual(response.status_code, 200)


class TestShowPlatform(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        platform = Platform.objects.get(name='ZX Spectrum')
        response = self.client.get('/platforms/%d/' % platform.id)
        self.assertEqual(response.status_code, 200)
