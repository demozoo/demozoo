# Generated by Django 4.0.8 on 2024-07-20 22:34

import base64
import re
from django.db import migrations


def decode_asciiarena_params(apps, schema_editor):
    ReleaserExternalLink = apps.get_model('demoscene', 'ReleaserExternalLink')
    for link in ReleaserExternalLink.objects.filter(link_class__in=['AsciiarenaArtist', 'AsciiarenaCrew']):
        name = base64.b64decode(link.parameter + "==").strip().decode('utf-8').lower()
        name = re.sub(r'\W+', '-', name)
        link.parameter = name
        link.save()

    ProductionLink = apps.get_model('productions', 'ProductionLink')
    for link in ProductionLink.objects.filter(link_class='AsciiarenaRelease'):
        link.parameter = base64.b64decode(link.parameter + "==").strip().decode('utf-8')
        link.save()


class Migration(migrations.Migration):

    dependencies = [
        ('demoscene', '0019_releaser_hide_from_search_engines'),
    ]

    operations = [
        migrations.RunPython(decode_asciiarena_params),
    ]