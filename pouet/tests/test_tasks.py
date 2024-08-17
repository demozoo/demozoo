from django.test import TestCase
from freezegun import freeze_time
from unittest.mock import patch

from demoscene.models import Releaser
from pouet.models import Group as PouetGroup
from pouet.models import Production as PouetProduction
from pouet.tasks import automatch_all_groups, automatch_group, pull_group, pull_groups
from productions.models import Production


@freeze_time('2020-01-15')
class TestTasks(TestCase):
    fixtures = ['tests/gasman.json', 'tests/pouet.json']

    @patch('pouet.tasks.automatch_group')
    def test_automatch_all_groups(self, automatch_group):
        hprg = Releaser.objects.get(name='Hooy-Program')
        hprg.external_links.create(link_class='PouetGroup', parameter='1218')

        automatch_all_groups()
        self.assertEqual(automatch_group.delay.call_count, 1)
        releaser_id, = automatch_group.delay.call_args.args
        self.assertEqual(releaser_id, hprg.id)

    def test_automatch_group(self):
        hprg = Releaser.objects.get(name='Hooy-Program')
        hprg.external_links.create(link_class='PouetGroup', parameter='1218')

        automatch_group(hprg.id)
        pondlife = Production.objects.get(title="Pondlife")
        self.assertTrue(pondlife.links.filter(link_class='PouetProduction', parameter='2611').exists())

    @patch('pouet.tasks.pull_group')
    def test_pull_groups(self, pull_group):
        hprg = Releaser.objects.get(name='Hooy-Program')
        hprg.external_links.create(link_class='PouetGroup', parameter='1218')

        pull_groups()
        pull_group.delay.assert_called_once_with('1218', hprg.id)

    def test_pull_group(self):
        ra = Releaser.objects.get(name='Raww Arse')
        pull_group('767', ra.id)
        self.assertTrue(PouetProduction.objects.filter(name='Bunch Of Arse').exists())
        self.assertTrue(PouetGroup.objects.filter(name='Jumalauta').exists())

    def test_pull_group_invalid(self):
        ra = Releaser.objects.get(name='Raww Arse')
        with self.assertLogs(level='WARNING'):
            pull_group('99999', ra.id)

    def test_pull_group_no_prods(self):
        ra = Releaser.objects.get(name='Raww Arse')
        pull_group('768', ra.id)
