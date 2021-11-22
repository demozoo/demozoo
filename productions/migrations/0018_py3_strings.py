# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-19 23:15
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productions', '0017_remove_ansi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credit',
            name='category',
            field=models.CharField(blank=True, choices=[('Code', 'Code'), ('Graphics', 'Graphics'), ('Music', 'Music'), ('Text', 'Text'), ('Other', 'Other')], max_length=20),
        ),
        migrations.AlterField(
            model_name='infofile',
            name='file',
            field=models.FileField(blank=True, upload_to='nfo'),
        ),
        migrations.AlterField(
            model_name='production',
            name='demozoo0_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Demozoo v0 ID'),
        ),
        migrations.AlterField(
            model_name='production',
            name='has_bonafide_edits',
            field=models.BooleanField(default=True, help_text='True if this production has been updated through its own forms, as opposed to just compo results tables'),
        ),
        migrations.AlterField(
            model_name='production',
            name='has_screenshot',
            field=models.BooleanField(default=False, editable=False, help_text='True if this prod has at least one (processed) screenshot'),
        ),
        migrations.AlterField(
            model_name='production',
            name='include_notes_in_search',
            field=models.BooleanField(default=True, help_text="Whether the notes field for this production will be indexed. (Untick this to avoid false matches in search results e.g. 'this demo was not by Magic / Nah-Kolor')"),
        ),
        migrations.AlterField(
            model_name='production',
            name='release_date_precision',
            field=models.CharField(blank=True, choices=[('d', 'Day'), ('m', 'Month'), ('y', 'Year')], max_length=1),
        ),
        migrations.AlterField(
            model_name='production',
            name='scene_org_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='scene.org ID'),
        ),
        migrations.AlterField(
            model_name='production',
            name='supertype',
            field=models.CharField(choices=[('production', 'Production'), ('graphics', 'Graphics'), ('music', 'Music')], db_index=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='productionblurb',
            name='body',
            field=models.TextField(help_text='A tweet-sized description of this demo, to promote it on listing pages'),
        ),
        migrations.AlterField(
            model_name='productionlink',
            name='demozoo0_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Demozoo v0 ID'),
        ),
        migrations.AlterField(
            model_name='productionlink',
            name='file_for_screenshot',
            field=models.CharField(blank=True, help_text='The file within this archive which has been identified as most suitable for generating a screenshot from', max_length=255),
        ),
        migrations.AlterField(
            model_name='productionlink',
            name='has_bad_image',
            field=models.BooleanField(default=False, help_text='Indicates that an attempt to create a screenshot from this link has failed at the image processing stage'),
        ),
        migrations.AlterField(
            model_name='productionlink',
            name='is_unresolved_for_screenshotting',
            field=models.BooleanField(default=False, help_text="Indicates that we've tried and failed to identify the most suitable file in this archive to generate a screenshot from"),
        ),
        migrations.AlterField(
            model_name='productionlink',
            name='source',
            field=models.CharField(blank=True, editable=False, help_text='Identifier to indicate where this link came from - e.g. manual (entered via form), match, auto', max_length=32),
        ),
        migrations.AlterField(
            model_name='productiontype',
            name='internal_name',
            field=models.CharField(blank=True, help_text='Used to identify this prod type for special treatment in code - leave this alone!', max_length=32),
        ),
        migrations.AlterField(
            model_name='productiontype',
            name='position',
            field=models.IntegerField(default=0, help_text='Position in which this should be ordered underneath its parent type (if not alphabetical)'),
        ),
    ]
