# Generated by Django 1.11.27 on 2020-02-05 22:10
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0004_event_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='intro',
            field=models.TextField(blank=True, help_text="Intro text to show on 'your recommendations' page - Markdown / HTML supported"),
        ),
    ]
