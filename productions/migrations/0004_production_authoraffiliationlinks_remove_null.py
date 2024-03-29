# Generated by Django 1.9.13 on 2017-10-22 00:20
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productions', '0003_increase_link_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='production',
            name='author_affiliation_nicks',
            field=models.ManyToManyField(blank=True, related_name='member_productions', to='demoscene.Nick'),
        ),
    ]
