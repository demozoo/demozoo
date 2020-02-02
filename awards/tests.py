# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from awards.models import Recommendation, Category
from productions.models import Production


class TestRecommendations(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.testuser = User.objects.create_user(username='testuser', password='12345')

    def test_recommendation_prompt_shown(self):
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        response = self.client.get('/productions/%d/' % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_recommendation_prompt_not_shown_for_old_prods(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get('/productions/%d/' % pondlife.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_categories_pre_ticked(self):
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/' % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            """<input id="award_recommendation_category_1" name="category_id" value="1" type="checkbox">""",
            html=True
        )
        self.assertContains(
            response,
            """<input id="award_recommendation_category_2" name="category_id" value="2" type="checkbox" checked="checked">""",
            html=True
        )
