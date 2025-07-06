from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from awards.models import Category, Event, EventSeries, Recommendation
from productions.models import Production, ProductionType


class TestModels(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_event_series_str(self):
        meteoriks = EventSeries.objects.get(name="Meteoriks")
        self.assertEqual(str(meteoriks), "Meteoriks")

    def test_event_str(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        self.assertEqual(str(meteoriks), "The Meteoriks 2020")

    def test_active_for_user(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        anon = AnonymousUser()
        user = User.objects.create_user(username="testuser", password="12345")

        # Events are active for anonymous and logged-in users when recommendations are enabled
        self.assertTrue(Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists())
        self.assertTrue(Event.active_for_user(user).filter(name="The Meteoriks 2020").exists())
        meteoriks.recommendations_enabled = False
        meteoriks.save()
        self.assertFalse(Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists())
        self.assertFalse(Event.active_for_user(user).filter(name="The Meteoriks 2020").exists())

        # Events are active for staff and jury members when reporting is enabled
        superuser = User.objects.create_superuser(
            username="testsuperuser", email="testsuperuser@example.com", password="12345"
        )
        self.assertTrue(Event.active_for_user(superuser).filter(name="The Meteoriks 2020").exists())
        meteoriks.jurors.create(user=user)
        self.assertTrue(Event.active_for_user(user).filter(name="The Meteoriks 2020").exists())

        # Events are not active for anyone if none of recommendations, screening or reporting are enabled
        meteoriks.reporting_enabled = False
        meteoriks.screening_enabled = False
        meteoriks.save()
        self.assertFalse(Event.active_for_user(anon).filter(name="The Meteoriks 2020").exists())
        self.assertFalse(Event.active_for_user(user).filter(name="The Meteoriks 2020").exists())
        self.assertFalse(Event.active_for_user(superuser).filter(name="The Meteoriks 2020").exists())

    def test_event_recommendation_options(self):
        meteoriks = Event.objects.get(name="The Meteoriks 2020")
        user = User.objects.create_user(username="testuser", password="12345")
        pondlife = Production.objects.get(title="Pondlife")
        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        best_lowend = Category.objects.get(name="Best Low-End Production")
        outstanding_concept = Category.objects.get(name="Outstanding Concept")

        Recommendation.objects.create(production=brexecutable, user=user, category=best_lowend)

        result = meteoriks.get_recommendation_options(user, brexecutable)
        self.assertEqual(
            result,
            [
                (best_lowend.pk, "Best Low-End Production", True),
                (outstanding_concept.pk, "Outstanding Concept", False),
            ],
        )

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
