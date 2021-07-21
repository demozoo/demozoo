from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout
from mock import patch

from parties.models import Party


class TestFetchTournaments(TestCase):
    fixtures = ['tests/gasman.json']

    @patch.object(Path, 'glob')
    @patch.object(Path, 'exists')
    @patch.object(Path, 'mkdir')
    @patch('tournaments.management.commands.fetch_tournaments.subprocess.run')
    def test_run_with_existing_repo(self, run, mkdir, exists, glob):
        exists.return_value = True
        data_path = Path(settings.FILEROOT) / 'tournaments' / 'test_data'
        glob.return_value = [
            data_path / '2011_shader_showdown_revision.json',
            data_path / '2011_shader_showdown_mystery_party.json',
            data_path / '2000_shader_showdown_forever.json',
        ]

        with captured_stdout():
            call_command('fetch_tournaments')

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / 'data' / 'livecode.demozoo.org'
        run.assert_called_once_with(['git', '-C', expected_path, 'pull'])
        glob.assert_called_once_with('*.json')

        party = Party.objects.get(name="Revision 2011")
        tournament = party.tournaments.get(name="Shader Showdown")
        self.assertTrue(tournament)
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")

        party = Party.objects.get(name="Forever 2e3")
        self.assertEqual(party.tournaments.count(), 1)
        tournament = party.tournaments.first()
        self.assertEqual(party.tournaments.count(), 1)
        # tournament data has not been updated, because filenames are mismatched
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")

    @patch.object(Path, 'glob')
    @patch.object(Path, 'exists')
    @patch.object(Path, 'mkdir')
    @patch('tournaments.management.commands.fetch_tournaments.subprocess.run')
    def test_run_without_existing_repo(self, run, mkdir, exists, glob):
        exists.return_value = False
        data_path = Path(settings.FILEROOT) / 'tournaments' / 'test_data'
        glob.return_value = [
            data_path / '2011_shader_showdown_revision.json',
            data_path / '2011_shader_showdown_mystery_party.json',
            data_path / '2000_z80_showdown_forever.json',
        ]

        with captured_stdout():
            call_command('fetch_tournaments')

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / 'data' / 'livecode.demozoo.org'
        run.assert_called_once_with([
            'git', 'clone', 'https://github.com/psenough/livecode.demozoo.org.git', expected_path
        ])
        glob.assert_called_once_with('*.json')

        party = Party.objects.get(name="Revision 2011")
        tournament = party.tournaments.get(name="Shader Showdown")
        self.assertTrue(tournament)
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")

        party = Party.objects.get(name="Forever 2e3")
        self.assertEqual(party.tournaments.count(), 1)
        tournament = party.tournaments.first()
        self.assertEqual(tournament.name, "Z80 Showdown")
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Semi-final")
