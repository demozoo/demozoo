import responses
from django.contrib.auth.models import AnonymousUser, User
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from requests.exceptions import HTTPError

from awards.models import Category, Event, EventSeries, Juror, Recommendation
from demoscene.models import SceneID
from productions.models import Production, ProductionType


class TestModels(TestCase):
    fixtures = ['tests/gasman.json']

    def test_event_series_str(self):
        meteoriks = EventSeries.objects.get(name="Meteoriks")
        self.assertEqual(str(meteoriks), "Meteoriks")

    def test_event_str(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        self.assertEqual(str(meteoriks), "The Meteoriks 2020")

    def test_active_for_user(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        anon = AnonymousUser()
        user = User.objects.create_user(username='testuser', password='12345')

        # Events are active for anonymous and logged-in users when recommendations are enabled
        self.assertTrue(
            Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists()
        )
        self.assertTrue(
            Event.active_for_user(user).filter(name="The Meteoriks 2020").exists()
        )
        meteoriks.recommendations_enabled = False
        meteoriks.save()
        self.assertFalse(
            Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists()
        )
        self.assertFalse(
            Event.active_for_user(user).filter(name="The Meteoriks 2020").exists()
        )

        # Events are active for staff and jury members when reporting is enabled
        superuser = User.objects.create_superuser(
            username='testsuperuser', email='testsuperuser@example.com', password='12345'
        )
        self.assertTrue(
            Event.active_for_user(superuser).filter(name="The Meteoriks 2020").exists()
        )
        meteoriks.jurors.create(user=user)
        self.assertTrue(
            Event.active_for_user(user).filter(name="The Meteoriks 2020").exists()
        )

        # Events are not active for anyone if neither recommendations nor reporting are enabled
        meteoriks.reporting_enabled = False
        meteoriks.save()
        self.assertFalse(
            Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists()
        )
        self.assertFalse(
            Event.active_for_user(user).filter(name="The Meteoriks 2020").exists()
        )
        self.assertFalse(
            Event.active_for_user(superuser).filter(name="The Meteoriks 2020").exists()
        )

    def test_event_recommendation_options(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        user = User.objects.create_user(username='testuser', password='12345')
        pondlife = Production.objects.get(title="Pondlife")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_highend = Category.objects.get(name="Best High-End Demo")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")

        Recommendation.objects.create(production=brexecutable, user=user, category=best_lowend)

        result = meteoriks.get_recommendation_options(user, brexecutable)
        self.assertEqual(result, [
            (best_lowend.pk, "Best Low-End Production", True),
            (outstanding_concept.pk, "Outstanding Concept", False),
        ])

        # no results for prods outside the date range
        result = meteoriks.get_recommendation_options(user, pondlife)
        self.assertEqual(result, [])

        # no results for prods of a non-eligible type
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        result = meteoriks.get_recommendation_options(user, brexecutable)
        self.assertEqual(result, [])

    def test_category_str(self):
        best_lowend = Category.objects.get(name="Best Low-End Production")
        self.assertEqual(str(best_lowend), "The Meteoriks 2020 - Best Low-End Production")


class TestCandidates(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/awards/meteoriks-2020/low-end/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

        response = self.client.get('/awards/meteoriks-2020/high-end/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

        response = self.client.get('/awards/meteoriks-2020/outstanding-concept/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Brexecutable Music Compo Is Over")
        self.assertNotContains(response, "Pondlife")

    def test_with_prod_type_limits(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        response = self.client.get('/awards/meteoriks-2020/low-end/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "The Brexecutable Music Compo Is Over")


class TestRecommendations(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.testuser = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='bob the commenter', password='password')

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

    def test_recommendation_prompt_not_shown_for_non_matching_prod_type(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        response = self.client.get('/productions/%d/' % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_recommendation_prompt_shown_for_matching_prod_type(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.production_types.add(ProductionType.objects.get(name="Intro"))
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        brexecutable.types.set([ProductionType.objects.get(name="4K Intro")])
        response = self.client.get('/productions/%d/' % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommend this production for The Meteoriks 2020!")

    def test_categories_pre_ticked(self):
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        best_highend = Category.objects.get(name="Best High-End Demo")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/productions/%d/' % brexecutable.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"""<input class="award-recommendation__checkbox" id="award_recommendation_category_{best_lowend.pk}" """
            f"""name="category_id" value="{best_lowend.pk}" type="checkbox" checked="checked">""",
            html=True
        )
        self.assertContains(
            response,
            f"""<input class="award-recommendation__checkbox" id="award_recommendation_category_{outstanding_concept.pk}" """
            f"""name="category_id" value="{outstanding_concept.pk}" type="checkbox">""",
            html=True
        )
        # not eligible for high-end, as per platform specifiers
        self.assertNotContains(
            response,
            f"""<input class="award-recommendation__checkbox" id="award_recommendation_category_{best_highend.pk}" """
            f"""name="category_id" value="{best_highend.pk}" type="checkbox">""",
            html=True
        )

    def test_post_recommendations(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username='testuser', password='12345')
        response = self.client.post('/awards/%s/recommend/%d/' % (meteoriks.slug, brexecutable.id), {
            'category_id': [outstanding_concept.id]
        })
        self.assertRedirects(response, '/productions/%d/' % brexecutable.id)

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

        self.client.login(username='testuser', password='12345')

        response = self.client.get('/awards/%s/' % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Brexecutable")
        self.assertContains(response, "You haven't made any recommendations yet.")

        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        response = self.client.get('/awards/%s/' % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable")
        self.assertNotContains(response, "You haven't made any recommendations yet.")

    def test_get_recommendations_no_login(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        response = self.client.get('/awards/%s/' % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in</a> to start making recommendations.")

    def test_recommendations_closed(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.recommendations_enabled = False
        meteoriks.save()
        response = self.client.get('/awards/%s/' % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Log in</a> to start making recommendations.")
        self.assertContains(response, "Recommendations are closed right now.")

    def test_remove_recommendation(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        rec = Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)

        self.client.login(username='testuser', password='12345')
        response = self.client.post('/awards/remove_recommendation/%d/' % (rec.id, ), {})
        self.assertRedirects(response, '/awards/%s/' % meteoriks.slug)
        self.assertEqual(Recommendation.objects.filter(user=self.testuser).count(), 0)

    def test_report_no_access(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/awards/%s/report/%d/' % (meteoriks.slug, best_lowend.id))
        self.assertEqual(response.status_code, 403)

    def test_report(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        Recommendation.objects.create(production=brexecutable, user=self.testuser, category=best_lowend)
        Recommendation.objects.create(production=brexecutable, user=self.other_user, category=best_lowend)
        Juror.objects.create(user=self.testuser, event=meteoriks)

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/awards/%s/report/%d/' % (meteoriks.slug, best_lowend.id))
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

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/awards/%s/report/%d/' % (meteoriks.slug, best_lowend.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable", 1)
        self.assertContains(response, "2 recommendations")

    def test_show_nominations(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend.nominations.create(production=brexecutable, status='nominee')

        response = self.client.get('/awards/%s/' % meteoriks.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brexecutable")


class TestFetchJurors(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        meteoriks.juror_feed_url = 'http://example.com/meteoriks-jurors.txt'
        meteoriks.save()

        self.testuser = User.objects.create_user(username='testuser', password='12345')
        self.truck = User.objects.create_user(username='truck', password='56789')
        SceneID.objects.create(user=self.testuser, sceneid=4242)
        SceneID.objects.create(user=self.truck, sceneid=666)
        Juror.objects.create(user=self.truck, event=meteoriks)

    @responses.activate
    def test_fetch_fail(self):
        exception = HTTPError('Something went wrong')
        responses.add(
            responses.GET, 'http://example.com/meteoriks-jurors.txt',
            body=exception
        )
        with captured_stdout():
            call_command('fetch_award_jurors')

        self.assertEqual(Juror.objects.filter(user=self.testuser).count(), 0)

    @responses.activate
    def test_fetch(self):
        responses.add(
            responses.GET, 'http://example.com/meteoriks-jurors.txt',
            body="4242  # testuser\n666  # truck\n"
        )
        call_command('fetch_award_jurors')

        self.assertEqual(Juror.objects.filter(user=self.testuser).count(), 1)
        self.assertEqual(Juror.objects.filter(user=self.truck).count(), 1)


class TestAwardsAdmin(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')

    def test_get(self):
        response = self.client.get('/admin/awards/category/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Meteoriks 2020")
        self.assertContains(response, "Best High-End Demo")
