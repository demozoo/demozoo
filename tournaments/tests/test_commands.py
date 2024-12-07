from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from demoscene.models import Nick
from demoscene.tests.utils import MediaTestMixin
from parties.models import Party


class TestFetchTournaments(MediaTestMixin, TestCase):
    fixtures = ["tests/gasman.json"]

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_run_with_existing_repo(self, run, mkdir, exists, glob):
        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2011_shader_showdown_revision.json",
            data_path / "2011_shader_showdown_mystery_party.json",
            data_path / "2000_shader_showdown_forever.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments")
        self.assertNotEqual(stdout.getvalue(), "")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

        party = Party.objects.get(name="Revision 2011")
        tournament = party.tournaments.get(name="Shader Showdown")
        self.assertTrue(tournament)
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")
        self.assertEqual(phase.staff.get(nick__name="LaesQ").role, "dj_set")
        yerz_orga = party.organisers.get(releaser__name="Yerzmyey")
        self.assertEqual(yerz_orga.role, "Shader Showdown")
        gasman_orga = party.organisers.get(releaser__name="Gasman")
        # already listed as an organiser, so no change
        self.assertEqual(gasman_orga.role, "Compo team")
        # stated role is something other than Organisers
        self.assertFalse(party.organisers.filter(releaser__name="LaesQ").exists())
        # nick doesn't match
        self.assertFalse(party.organisers.filter(releaser__name="Abyss").exists())
        gasman_entry = phase.entries.get(nick__name="Gasman")
        self.assertEqual(gasman_entry.ranking, "1")
        self.assertEqual(gasman_entry.original_image_sha1, "bae1b44bb69fdb36ee86e689a2df876ae22e0dc5")
        entry2 = phase.entries.get(name="Mr Phong")
        self.assertEqual(entry2.external_links.get(link_class="Tic80Cart").parameter, "2308")
        self.assertNotEqual(entry2.thumbnail_url, "")

        party = Party.objects.get(name="Forever 2e3")
        self.assertEqual(party.tournaments.count(), 1)
        tournament = party.tournaments.first()
        self.assertEqual(party.tournaments.count(), 1)
        # tournament data has not been updated, because filenames are mismatched
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_run_without_existing_repo(self, run, mkdir, exists, glob):
        exists.return_value = False
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2011_shader_showdown_revision.json",
            data_path / "2011_shader_showdown_mystery_party.json",
            data_path / "2000_z80_showdown_forever.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments", silent=True)
        self.assertEqual(stdout.getvalue(), "")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(
            ["git", "clone", "https://github.com/psenough/livecode.demozoo.org.git", expected_path, "--quiet"]
        )
        glob.assert_called_once_with("*.json")

        party = Party.objects.get(name="Revision 2011")
        tournament = party.tournaments.get(name="Shader Showdown")
        self.assertTrue(tournament)
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Final")
        entry = phase.entries.get(nick__name="Gasman")
        self.assertEqual(
            entry.source_file, "https://files.scene.org/view/parties/2011/revision11/shadershowdown/03-gasman.glsl"
        )

        party = Party.objects.get(name="Forever 2e3")
        self.assertEqual(party.tournaments.count(), 1)
        tournament = party.tournaments.first()
        self.assertEqual(tournament.name, "Z80 Showdown")
        phase = tournament.phases.first()
        self.assertEqual(phase.name, "Semi-final")

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_party_mismatch(self, run, mkdir, exists, glob):
        """
        obscure warning where a data file that was previously associated with
        party X now seems to contain data corresponding to party Y instead
        """
        party = Party.objects.get(name="Forever 2e3")
        tournament = party.tournaments.first()
        tournament.source_file_name = "2011_shader_showdown_revision.json"
        tournament.save()

        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2011_shader_showdown_revision.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

        self.assertIn("Party mismatch! Found Forever 2e3, but data looks like Revision 2011", stdout.getvalue())

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_exception_raised_on_duplicate_nicks(self, run, mkdir, exists, glob):
        Nick.objects.get(name="Shingebis").variants.create(name="gasman")
        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2011_shader_showdown_revision.json",
        ]

        with self.assertRaisesRegex(Exception, r"Multiple nicks found for gasman \(Gasman\)"):
            with captured_stdout():
                call_command("fetch_tournaments")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

    @patch("tournaments.management.commands.fetch_tournaments.mail_admins")
    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_email_sent_on_duplicate_nicks_in_silent_mode(self, run, mkdir, exists, glob, mail_admins):
        Nick.objects.get(name="Shingebis").variants.create(name="gasman")
        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2011_shader_showdown_revision.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments", silent=True)
        self.assertEqual(stdout.getvalue(), "")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull", "--quiet"])
        glob.assert_called_once_with("*.json")
        mail_admins.assert_called_once()
        subject, body = mail_admins.call_args.args
        self.assertEqual(subject, "Error importing tournament data")
        self.assertIn("Multiple nicks found for gasman (Gasman)", body)

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_reimport_phases_if_counts_differ(self, run, mkdir, exists, glob):
        party = Party.objects.get(name="Forever 2e3")
        tournament = party.tournaments.first()
        tournament.phases.create(name="Quarter final", position=2)

        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2000_z80_showdown_forever.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

        self.assertIn("Phases don't match - recreating", stdout.getvalue())
        self.assertEqual(tournament.phases.count(), 1)
        phase = tournament.phases.first()
        entry = phase.entries.get(name="Mr Phong")
        self.assertNotEqual(entry.thumbnail_url, "")

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_dont_reimport_phases_if_all_names_match(self, run, mkdir, exists, glob):
        party = Party.objects.get(name="Forever 2e3")
        tournament = party.tournaments.first()
        phase = tournament.phases.first()
        phase.name = "Semi-final"
        phase.save()
        gasman_entry = phase.entries.get(name="Gasman")
        gasman_entry.original_image_sha1 = "1234123412341234"
        gasman_entry.thumbnail_url = "http://example.com/original.png"
        gasman_entry.save()

        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2000_z80_showdown_forever.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

        self.assertNotIn("Phases don't match - recreating", stdout.getvalue())
        self.assertEqual(tournament.phases.count(), 1)
        self.assertEqual(tournament.phases.first(), phase)
        gasman_entry = phase.entries.get(name="fake gasman")
        self.assertEqual(gasman_entry.ranking, "1")
        self.assertEqual(gasman_entry.original_image_sha1, "bae1b44bb69fdb36ee86e689a2df876ae22e0dc5")
        self.assertNotEqual(gasman_entry.thumbnail_url, "http://example.com/original.png")

    @patch.object(Path, "glob")
    @patch.object(Path, "exists")
    @patch.object(Path, "mkdir")
    @patch("tournaments.management.commands.fetch_tournaments.subprocess.run")
    def test_dont_replace_screenshot_if_sha1_matches(self, run, mkdir, exists, glob):
        party = Party.objects.get(name="Forever 2e3")
        tournament = party.tournaments.first()
        phase = tournament.phases.first()
        phase.name = "Semi-final"
        phase.save()
        gasman_entry = phase.entries.get(name="Gasman")
        gasman_entry.original_image_sha1 = "bae1b44bb69fdb36ee86e689a2df876ae22e0dc5"
        gasman_entry.thumbnail_url = "http://example.com/original.png"
        gasman_entry.save()

        exists.return_value = True
        data_path = Path(settings.FILEROOT) / "tournaments" / "test_data"
        glob.return_value = [
            data_path / "2000_z80_showdown_forever.json",
        ]

        with captured_stdout() as stdout:
            call_command("fetch_tournaments")

        mkdir.assert_called_once_with(exist_ok=True)
        expected_path = Path(settings.FILEROOT) / "data" / "livecode.demozoo.org"
        run.assert_called_once_with(["git", "-C", expected_path, "pull"])
        glob.assert_called_once_with("*.json")

        self.assertNotIn("Phases don't match - recreating", stdout.getvalue())
        self.assertEqual(tournament.phases.count(), 1)
        self.assertEqual(tournament.phases.first(), phase)
        gasman_entry = phase.entries.get(name="fake gasman")
        self.assertEqual(gasman_entry.ranking, "1")
        self.assertEqual(gasman_entry.original_image_sha1, "bae1b44bb69fdb36ee86e689a2df876ae22e0dc5")
        self.assertEqual(gasman_entry.thumbnail_url, "http://example.com/original.png")
