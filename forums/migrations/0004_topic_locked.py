# Generated by Django 4.0.10 on 2024-08-17 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0003_topic_residue'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]
