# Generated by Django 1.11.29 on 2020-11-19 23:15
from django.db import migrations, models

import homepage.models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0002_banner_hide_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banner',
            name='hide_text',
            field=models.BooleanField(default=False, help_text="Instead of displaying text, use it as fallback text for people who can't see the image"),
        ),
        migrations.AlterField(
            model_name='banner',
            name='url',
            field=models.CharField(max_length=255, verbose_name='URL'),
        ),
        migrations.AlterField(
            model_name='bannerimage',
            name='image',
            field=models.ImageField(height_field='image_height', help_text='Will be cropped to 2.5 : 1 aspect ratio. Recommended size: 832x333', upload_to=homepage.models.banner_image_upload_to, width_field='image_width'),
        ),
        migrations.AlterField(
            model_name='newsimage',
            name='image',
            field=models.ImageField(height_field='image_height', help_text='Recommended size: 100x100', upload_to=homepage.models.news_image_upload_to, width_field='image_width'),
        ),
    ]
