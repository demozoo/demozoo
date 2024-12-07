from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from demoscene.models import Nick
from productions.models import Production


class TestNewcomersReport(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_run(self):
        madrielle = Production.objects.get(title="Madrielle")
        madrielle.author_affiliation_nicks.add(Nick.objects.get(name="Future Crew"))
        madrielle.credits.create(nick=Nick.objects.get(name="Ra"), role="code")

        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        brexecutable.credits.create(nick=Nick.objects.get(name="Abyss"), role="code")
        brexecutable.credits.create(nick=Nick.objects.get(name="Future Crew"), role="code")
        brexecutable.credits.create(nick=Nick.objects.get(name="Ra"), role="code")
        with captured_stdout() as stdout:
            call_command("newcomers_report", "2019")
        self.assertEqual(stdout.getvalue(), "Abyss,https://demozoo.org/sceners/8/\n")
