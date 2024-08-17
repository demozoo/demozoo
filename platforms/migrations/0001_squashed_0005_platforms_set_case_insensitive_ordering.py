# Generated by Django 5.0.8 on 2024-08-17 13:21

import django.db.models.deletion
import django.db.models.functions.text
import platforms.models
from django.db import migrations, models


def make_default_platforms(apps, schema):
    Platform = apps.get_model('platforms', 'Platform')
    if Platform.objects.exists():
        return
    platforms = [
        {'name': 'ZX Spectrum'},
        {'name': 'Windows'},
        {'name': 'Commodore 64'},
        {'name': 'MS-Dos'},
        {'name': 'Amiga OCS/ECS'},
        {'name': 'Amiga AGA'},
        {'name': 'Linux'},
        {'name': 'BeOS'},
        {'name': 'Atari ST/E'},
        {'name': 'Mac OS X'},
        {'name': 'Browser'},
        {'name': 'Sony Playstation 1 (PSX)'},
        {'name': 'Console Handheld'},
        {'name': 'XBOX360'},
        {'name': 'Atari 8 bit'},
        {'name': 'Atari Falcon'},
        {'name': 'Mobile'},
        {'name': 'VIC-20'},
        {'name': 'Sega Megadrive/Genesis'},
        {'name': 'Sega Dreamcast'},
        {'name': 'Nintendo Wii'},
        {'name': 'Nintendo Entertainment System (NES)'},
        {'name': 'Amiga PPC/RTG'},
        {'name': 'Calculator'},
        {'name': 'Sony Playstation 2 (PS2)'},
        {'name': 'Sony Playstation Portable (PSP)'},
        {'name': 'Nintendo GameBoy Advance (GBA)'},
        {'name': 'MSX'},
        {'name': 'Nintendo DS (NDS)'},
        {'name': 'Nintendo SNES/Super FamiCom'},
        {'name': 'Acorn Archimedes'},
        {'name': 'Amstrad CPC'},
        {'name': 'Nintendo GameBoy Color (GBC)'},
        {'name': 'Nintendo GameBoy (GB)'},
        {'name': 'Nintendo 64 (N64)'},
        {'name': 'XBOX'},
        {'name': 'Commodore 16/Plus 4'},
        {'name': 'KC 85/Robotron KC 87'},
        {'name': 'Vectrex'},
        {'name': 'Sega Master System'},
        {'name': 'ZX81'},
        {'name': 'Javascript'},
        {'name': 'Flash'},
        {'name': 'Java'},
        {'name': 'Oric'},
        {'name': 'Atari Jaguar'},
        {'name': 'SAM Coupé'},
        {'name': 'Android'},
        {'name': 'Thomson'},
        {'name': 'Atari 2600 Video Computer System (VCS)'},
        {'name': 'Commodore 128'},
        {'name': 'Gamepark GP2X'},
        {'name': 'Apple II GS'},
        {'name': 'Atari TT'},
        {'name': 'Raspberry Pi'},
        {'name': 'Nintendo GameCube (NGC)'},
        {'name': 'Amstrad Plus'},
        {'name': 'Custom Hardware'},
        {'name': 'PMD 85'},
        {'name': 'Paper'},
        {'name': 'Vector-06C'},
        {'name': 'BBC Micro'},
        {'name': 'Apple II'},
        {'name': 'Sony Playstation 3 (PS3)'},
        {'name': 'ZX Spectrum Enhanced'},
        {'name': 'Atari Lynx'},
        {'name': 'Nintendo 3DS'},
        {'name': 'Gamepark 32 '},
        {'name': 'Electronika BK-0010/11M'},
        {'name': 'Enterprise'},
        {'name': 'NEC PC Engine'},
    ]

    for platform in platforms:
        Platform.objects.create(**platform)


class Migration(migrations.Migration):

    replaces = [('platforms', '0001_initial'), ('platforms', '0002_default_platforms'), ('platforms', '0003_platformalias'), ('platforms', '0004_py3_strings'), ('platforms', '0005_platforms_set_case_insensitive_ordering')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('intro_text', models.TextField(blank=True)),
                ('photo', models.ImageField(blank=True, height_field=b'photo_height', null=True, upload_to=platforms.models.photo_original_upload_to, width_field=b'photo_width')),
                ('photo_width', models.IntegerField(blank=True, editable=False, null=True)),
                ('photo_height', models.IntegerField(blank=True, editable=False, null=True)),
                ('photo_url', models.CharField(blank=True, editable=False, max_length=255)),
                ('thumbnail', models.ImageField(blank=True, editable=False, height_field=b'thumbnail_height', null=True, upload_to=platforms.models.thumbnail_upload_to, width_field=b'thumbnail_width')),
                ('thumbnail_width', models.IntegerField(blank=True, editable=False, null=True)),
                ('thumbnail_height', models.IntegerField(blank=True, editable=False, null=True)),
                ('thumbnail_url', models.CharField(blank=True, editable=False, max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(
            code=make_default_platforms,
        ),
        migrations.AlterField(
            model_name='platform',
            name='photo',
            field=models.ImageField(blank=True, height_field='photo_height', null=True, upload_to=platforms.models.photo_original_upload_to, width_field='photo_width'),
        ),
        migrations.AlterField(
            model_name='platform',
            name='thumbnail',
            field=models.ImageField(blank=True, editable=False, height_field='thumbnail_height', null=True, upload_to=platforms.models.thumbnail_upload_to, width_field='thumbnail_width'),
        ),
        migrations.CreateModel(
            name='PlatformAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Alternative name to be recognised in search filters such as platform:c64', max_length=255)),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='platforms.platform')),
            ],
        ),
        migrations.AlterModelOptions(
            name='platform',
            options={'ordering': [django.db.models.functions.text.Lower('name')]},
        ),
    ]
