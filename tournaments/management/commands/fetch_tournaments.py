import json
import subprocess
import traceback
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand

from tournaments.importing import import_tournament


REPO_URL = "https://github.com/psenough/livecode.demozoo.org.git"
DATA_PATH = Path(settings.FILEROOT) / "data"
LOCAL_REPO_PATH = DATA_PATH / "livecode.demozoo.org"
TOURNAMENT_DATA_PATH = LOCAL_REPO_PATH / "public" / "data"
try:
    # only intended for use in the test environment
    TOURNAMENT_MEDIA_PATH = Path(settings.TOURNAMENT_MEDIA_PATH)
except AttributeError:  # pragma: no cover
    TOURNAMENT_MEDIA_PATH = LOCAL_REPO_PATH / "public" / "media"


class Command(BaseCommand):
    help = "Imports tournament data from livecode.demozoo.org"

    def add_arguments(self, parser):
        parser.add_argument(
            "--silent",
            action="store_true",
            help="Run silently and email admins on error",
        )

    def handle(self, *args, silent=False, **options):
        if silent:
            self.stdout = StringIO()

        try:
            # Clone or pull the livecode.demozoo.org repo
            DATA_PATH.mkdir(exist_ok=True)

            if LOCAL_REPO_PATH.exists():
                command = ["git", "-C", LOCAL_REPO_PATH, "pull"]
            else:
                command = ["git", "clone", REPO_URL, LOCAL_REPO_PATH]

            if silent:
                command.append("--quiet")
            subprocess.run(command)

            # loop over .json files in public/data
            for path in TOURNAMENT_DATA_PATH.glob("*.json"):
                print(path.name, file=self.stdout)
                with path.open() as f:
                    tournament_data = json.loads(f.read())

                import_tournament(path.name, tournament_data, TOURNAMENT_MEDIA_PATH, stdout=self.stdout)

        except Exception as e:
            if silent:
                mail_admins(
                    "Error importing tournament data",
                    "Error:\n\n%s\n\nOutput:\n\n%s" % ("".join(traceback.format_exception(e)), self.stdout.getvalue()),
                    fail_silently=True,
                )
            else:
                raise
