from django.test import TestCase

from tournaments.models import Tournament


class TestModels(TestCase):
    fixtures = ['tests/gasman.json']

    def test_string(self):
        tournament = Tournament.objects.get(name="Shader Showdown", party__name="Forever 2e3")
        self.assertEqual(str(tournament), "Shader Showdown at Forever 2e3")

        phase = tournament.phases.get(name="Final")
        self.assertEqual(str(phase), "Final")

        entry = phase.entries.get(nick__name="Gasman")
        self.assertEqual(str(entry), "Gasman")

    def test_has_rankings_and_scores(self):
        tournament = Tournament.objects.get(name="Shader Showdown", party__name="Forever 2e3")
        phase = tournament.phases.get(name="Final")
        self.assertTrue(phase.has_rankings)
        self.assertTrue(phase.has_scores)
