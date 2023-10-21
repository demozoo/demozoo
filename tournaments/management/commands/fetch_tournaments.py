import json
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from tournaments.importing import import_tournament


REPO_URL = 'https://github.com/psenough/livecode.demozoo.org.git'
DATA_PATH = Path(settings.FILEROOT) / 'data'
LOCAL_REPO_PATH = DATA_PATH / 'livecode.demozoo.org'
TOURNAMENT_DATA_PATH = LOCAL_REPO_PATH / 'public' / 'data'
try:
    # only intended for use in the test environment
    TOURNAMENT_MEDIA_PATH = Path(settings.TOURNAMENT_MEDIA_PATH)
except AttributeError:  # pragma: no cover
    TOURNAMENT_MEDIA_PATH = LOCAL_REPO_PATH / 'public' / 'media'


class Command(BaseCommand):
    help = 'Imports tournament data from livecode.demozoo.org'

    def handle(self, *args, **options):
        # Clone or pull the livecode.demozoo.org repo
        DATA_PATH.mkdir(exist_ok=True)

        if LOCAL_REPO_PATH.exists():
            subprocess.run([
                'git', '-C', LOCAL_REPO_PATH, 'pull'
            ])
        else:
            subprocess.run([
                'git', 'clone', REPO_URL, LOCAL_REPO_PATH
            ])

        # loop over .json files in public/data
        for path in TOURNAMENT_DATA_PATH.glob('*.json'):
            print(path.name)
            with path.open() as f:
                tournament_data = json.loads(f.read())

            import_tournament(path.name, tournament_data, TOURNAMENT_MEDIA_PATH)
