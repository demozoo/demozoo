# Generated by Django 4.0.8 on 2023-10-15 20:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parties', '0014_populate_party_series_external_links'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partyseries',
            name='pouet_party_id',
        ),
        migrations.RemoveField(
            model_name='partyseries',
            name='twitter_username',
        ),
    ]
