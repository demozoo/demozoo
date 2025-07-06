from django.contrib.auth.models import User
from django.test import TestCase

from awards.models import Category, Event, Juror, Recommendation
from productions.models import Production, ProductionType


class TestCandidates(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_get(self):
        response = self.client.get("/awards/meteoriks-2020/low-end/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

        response = self.client.get("/awards/meteoriks-2020/high-end/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

        response = self.client.get("/awards/meteoriks-2020/outstanding-concept/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

    def test_with_prod_type_limits(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        response = self.client.get("/awards/meteoriks-2020/low-end/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "The Brexecutable Music Compo Is Over")


class TestRecommendations(TestCase):
    fixtures = ["tests/gasman.json"]

    def setUp(self):
        self.testuser = User.objects.create_user(username="testuser", password="12345")
        self.other_user = User.objects.create_user(username="bob the commenter", password="password")

    def test_recommendation_prompt_shown(self):
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        response = self.client.get("/productions/%d/" % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_recommendation_prompt_not_shown_for_old_prods(self):
        pondlife = Production.objects.get(title="Pondlife")
        response = self.client.get("/productions/%d/" % pondlife.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_recommendation_prompt_not_shown_for_non_matching_prod_type(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        response = self.client.get("/productions/%d/" % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_recommendation_prompt_shown_for_matching_prod_type(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        brexecutable.types.set([ProductionType.objects.get(name="4K Intro")])
        response = self.client.get("/productions/%d/" % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_categories_pre_ticked(self):
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        best_highend = Category.objects.get(name="Best High-End Demo")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username="testuser", password="12345")
        response = self.client.get("/productions/%d/" % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"""<input class="award-recommendation__checkbox" id="award_recommendation_category_{best_lowend.pk}" """
            f"""name="category_id" value="{best_lowend.pk}" type="checkbox" checked="checked">""",
            html=True,
        )
        self.assertContains(
            response,
            f"""<input class="award-recommendation__checkbox" """
            f"""id="award_recommendation_category_{outstanding_concept.pk}" """
            f"""name="category_id" value="{outstanding_concept.pk}" type="checkbox">""",
            html=True,
        )
        # not eligible for high-end, as per platform specifiers
        self.assertNotContains(
            response,
            f"""<input class="award-recommendation__checkbox" id="award_recommendation_category_{best_highend.pk}" """
            f"""name="category_id" value="{best_highend.pk}" type="checkbox">""",
            html=True,
        )

    def test_post_recommendations(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            "/awards/%s/recommend/%d/" % (meteoriks.slug, brexecutable.id), {"category_id": [outstanding_concept.id]}
        )
        self.assertRedirects(response, "/productions/%d/" % brexecutable.id)

        self.assertTrue(
            Recommendation.objects.filter(
                user=self.testuser, production=brexecutable, category=outstanding_concept
            ).exists()
        )
        self.assertFalse(
            Recommendation.objects.filter(user=self.testuser, production=brexecutable, category=best_lowend).exists()
        )

    def test_get_recommendations(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")

        self.client.login(username="testuser", password="12345")

        response = self.client.get("/awards/%s/" % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Brexecutable")
        self.assertContains(response, "You haven't made any recommendations yet.")

        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        response = self.client.get("/awards/%s/" % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable")
        self.assertNotContains(response, "You haven't made any recommendations yet.")

    def test_get_recommendations_no_login(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        response = self.client.get("/awards/%s/" % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in</a> to start making recommendations.")

    def test_recommendations_closed(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.recommendations_enabled = False
        meteoriks.save()
        response = self.client.get("/awards/%s/" % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Log in</a> to start making recommendations.")
        self.assertContains(response, "Recommendations are closed right now.")

    def test_remove_recommendation(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        rec = Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username="testuser", password="12345")
        response = self.client.post("/awards/remove_recommendation/%d/" % (rec.id,), {})
        self.assertRedirects(response, "/awards/%s/" % meteoriks.slug)
        self.assertEqual(Recommendation.objects.filter(user=self.testuser).count(), 0)

    def test_report_no_access(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")

        self.client.login(username="testuser", password="12345")
        response = self.client.get("/awards/%s/report/%d/" % (meteoriks.slug, best_lowend.id))
        self.assertEqual(response.status_code, 403)

    def test_report(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)
        Recommendation.objects.create(production=brexecutable, user=self.other_user, category=best_lowend)
        Juror.objects.create(user=self.testuser, event=meteoriks)

        self.client.login(username="testuser", password="12345")
        response = self.client.get("/awards/%s/report/%d/" % (meteoriks.slug, best_lowend.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable", 1)
        self.assertNotContains(response, "2 recommendations")

    def test_report_with_counts(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.show_recommendation_counts = True
        meteoriks.save()
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)
        Recommendation.objects.create(production=brexecutable, user=self.other_user, category=best_lowend)
        Juror.objects.create(user=self.testuser, event=meteoriks)

        self.client.login(username="testuser", password="12345")
        response = self.client.get("/awards/%s/report/%d/" % (meteoriks.slug, best_lowend.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable", 1)
        self.assertContains(response, "2 recommendations")

    def test_show_nominations(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend.nominations.create(production=brexecutable, status="nominee")

        response = self.client.get("/awards/%s/" % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable")
        self.assertContains(response, '<a href="/awards/meteoriks-2019/">2019</a>', html=True)
        # 2021 has no nominations
        self.assertNotContains(response, '<a href="/awards/meteoriks-2021/">2021</a>', html=True)
