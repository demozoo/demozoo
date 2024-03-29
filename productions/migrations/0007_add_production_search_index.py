# Generated by Django 1.11.8 on 2018-01-06 00:04
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productions', '0006_remove_production_default_screenshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='production',
            name='search_document',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name='production',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_document'], name='productions_search__8683f0_gin'),
        ),
    ]
