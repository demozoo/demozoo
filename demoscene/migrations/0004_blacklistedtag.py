# Generated by Django 1.9.13 on 2017-09-21 22:55
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demoscene', '0003_increase_link_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlacklistedTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(help_text=b'The tag to be blacklisted', max_length=255)),
                ('replacement', models.CharField(blank=True, help_text=b'What to replace the tag with (leave blank to delete it completely)', max_length=255)),
                ('message', models.TextField(blank=True, help_text=b'Message to show to the user when they try to use the tag (optional)')),
            ],
        ),
    ]
