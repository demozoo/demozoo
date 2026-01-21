from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from demoscene.models import Nick, Releaser
from productions.models import Production, ProductionType


class TestNewcomersReport(TestCase):
    fixtures = ["tests/gasman.json"]

    def test_run(self):
        rez = Releaser.objects.create(name="Rez", is_group=False)
        razor_1911 = Releaser.objects.create(name="Razor 1911", is_group=True)

        madrielle = Production.objects.get(title="Madrielle")
        madrielle.author_affiliation_nicks.add(Nick.objects.get(name="Future Crew"))
        madrielle.credits.create(nick=Nick.objects.get(name="Ra"), role="code")

        brexecutable = Production.objects.get(title="The Brexecutable Music Compo Is Over")
        brexecutable.credits.create(nick=Nick.objects.get(name="Abyss"), role="code")
        brexecutable.credits.create(nick=Nick.objects.get(name="Future Crew"), role="code")
        brexecutable.credits.create(nick=Nick.objects.get(name="Ra"), role="code")
        brexecutable.author_nicks.add(Nick.objects.get(name="Rez"))
        brexecutable.author_nicks.add(Nick.objects.get(name="Razor 1911"))

        votedisk = Production.objects.create(
            title="We have accidentally borrowed your votedisk",
            release_date_date="2019-05-01",
            release_date_precision="d",
            supertype="production",
        )
        votedisk.types.add(ProductionType.objects.get(name="64K Intro"))
        votedisk.author_nicks.add(Nick.objects.get(name="Rez"))
        votedisk.author_affiliation_nicks.add(Nick.objects.get(name="Razor 1911"))

        with captured_stdout() as stdout:
            call_command("newcomers_report", "2019")
        lines = stdout.getvalue().strip().split("\n")
        self.assertCountEqual(
            lines,
            [
                "Abyss,https://demozoo.org/sceners/8/,0",
                "Razor 1911,https://demozoo.org/groups/%d/,0" % razor_1911.id,
                "Rez,https://demozoo.org/sceners/%d/,0" % rez.id,
            ],
        )
