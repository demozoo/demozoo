# Generated by Django 3.2.12 on 2022-03-03 22:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pouet', '0002_groupmatchinfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField()),
                ('link_type', models.CharField(max_length=255)),
                ('production', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='download_links', to='pouet.production')),
            ],
        ),
    ]
