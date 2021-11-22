# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-10-07 17:26
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoscene', '0009_search_document_noneditable'),
        ('pouet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMatchInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matched_production_count', models.IntegerField()),
                ('unmatched_demozoo_production_count', models.IntegerField()),
                ('unmatched_pouet_production_count', models.IntegerField()),
                ('releaser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='demoscene.Releaser')),
            ],
        ),
    ]
