from __future__ import absolute_import, unicode_literals

import json

from django.contrib.auth.models import User
from django.test import TestCase

from parties.models import Competition
from platforms.models import Platform
from productions.models import Production, ProductionType


class TestAddPlacing(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_post_with_platform_and_prodtype(self):
        competition = Competition.objects.get(party__name="Forever 2e3", name="ZX 1K Intro")
        zx_spectrum = Platform.objects.get(name='ZX Spectrum')
        one_k_intro = ProductionType.objects.get(name='1K Intro')

        response = self.client.post(
            '/competition_api/add_placing/%d/' % competition.id,
            json.dumps({
                'position': 1,
                'production': {
                    'title': "Artifice",
                    'byline': {'authors': [], 'affiliations': []},
                    'platform_id': zx_spectrum.id, 'production_type_id': one_k_intro.id,
                },
                'ranking': '1',
                'score': '',
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(competition.placings.get(position=1).ranking, '1')
        self.assertTrue(Production.objects.filter(title="Artifice").exists())

    def test_post_without_platform_and_prodtype(self):
        competition = Competition.objects.get(party__name="Forever 2e3", name="ZX 1K Intro")

        response = self.client.post(
            '/competition_api/add_placing/%d/' % competition.id,
            json.dumps({
                'position': 1,
                'production': {
                    'title': "Artifice",
                    'byline': {'authors': [], 'affiliations': []},
                    'platform_id': None, 'production_type_id': None,
                },
                'ranking': '1',
                'score': '',
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(competition.placings.get(position=1).ranking, '1')
        self.assertTrue(Production.objects.filter(title="Artifice").exists())

    def test_post_with_unresolved_name(self):
        competition = Competition.objects.get(party__name="Forever 2e3", name="ZX 1K Intro")

        response = self.client.post(
            '/competition_api/add_placing/%d/' % competition.id,
            json.dumps({
                'position': 1,
                'production': {
                    'title': "Artifice",
                    'byline': {
                        'authors': [{'id': '9999', 'name': 'SerzhSoft'}],
                        'affiliations': [{'id': '9999', 'name': 'SerzhSoft Allstars'}]
                    },
                    'platform_id': None, 'production_type_id': None,
                },
                'ranking': '1',
                'score': '',
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(competition.placings.get(position=1).ranking, '1')
        self.assertEqual(Production.objects.get(title="Artifice").unparsed_byline, 'SerzhSoft / SerzhSoft Allstars')


class TestUpdatePlacing(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        self.competition = Competition.objects.get(party__name="Forever 2e3", name="ZX 1K Intro")
        self.madrielle = Production.objects.get(title="Madrielle")
        self.madrielle_placing = self.competition.placings.get(production=self.madrielle)
        self.mathricks = Production.objects.create(title="Mathricks", supertype="production")
        self.mathricks_placing = self.competition.placings.create(
            position=2, production=self.mathricks, ranking='3'
        )

    def test_post_move_down(self):
        response = self.client.post(
            '/competition_api/update_placing/%d/' % self.madrielle_placing.id,
            json.dumps({
                'position': 2,
                'production': {
                    'id': self.madrielle.id,
                    'title': "Madrielle",
                    'byline': {'authors': [], 'affiliations': []},
                    'platform_id': None, 'production_type_id': None,
                },
                'ranking': '2',
                'score': '123',
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.competition.placings.get(position=2).score, '123')

    def test_post_move_up(self):
        response = self.client.post(
            '/competition_api/update_placing/%d/' % self.mathricks_placing.id,
            json.dumps({
                'position': 1,
                'production': {
                    'id': self.mathricks.id,
                    'title': "Mathricks",
                    'byline': {'authors': [], 'affiliations': []},
                    'platform_id': None, 'production_type_id': None,
                },
                'ranking': '3',
                'score': '123',
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.competition.placings.get(position=1).score, '123')


class TestDeletePlacing(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        self.competition = Competition.objects.get(party__name="Forever 2e3", name="ZX 1K Intro")
        self.madrielle = Production.objects.get(title="Madrielle")
        self.madrielle_placing = self.competition.placings.get(production=self.madrielle)
        self.mathricks = Production.objects.create(
            title="Mathricks", supertype="production", has_bonafide_edits=False
        )
        self.mathricks_placing = self.competition.placings.create(
            position=2, production=self.mathricks, ranking='3'
        )

    def test_post(self):
        response = self.client.post('/competition_api/delete_placing/%d/' % self.mathricks_placing.id, {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.competition.placings.count(), 1)
        self.assertFalse(Production.objects.filter(title="Mathricks").exists())

    def test_do_not_delete_prod_with_bonafide_edits(self):
        response = self.client.post('/competition_api/delete_placing/%d/' % self.madrielle_placing.id, {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.competition.placings.count(), 1)
        self.assertTrue(Production.objects.filter(title="Madrielle").exists())
