import os
import pathlib
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand

REPO_URL = 'https://github.com/psenough/livecode.demozoo.org.git'
DATA_PATH = os.path.join(os.path.abspath(settings.FILEROOT), 'data')
LOCAL_REPO_PATH = os.path.join(DATA_PATH, 'livecode.demozoo.org')


class Command(BaseCommand):
    help = 'Imports tournament data from livecode.demozoo.org'

    def handle(self, *args, **options):
        pathlib.Path(DATA_PATH).mkdir(exist_ok=True)

        if os.path.exists(LOCAL_REPO_PATH):
            subprocess.run([
                'git', '-C', LOCAL_REPO_PATH, 'pull'
            ])
        else:
            subprocess.run([
                'git', 'clone', REPO_URL, LOCAL_REPO_PATH
            ])
