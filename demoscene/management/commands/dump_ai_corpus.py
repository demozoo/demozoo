# output a whole load of text sourced from our notes

import re

from django.core.management.base import BaseCommand

from demoscene.models import Releaser
from productions.models import Production


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for model in [Production, Releaser]:
            for note in model.objects.exclude(notes="").values_list("notes", flat=True):
                note = re.sub(r"https?://\S+", "", note)
                print(note)
