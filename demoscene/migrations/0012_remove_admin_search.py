# Generated by Django 1.11.27 on 2020-01-02 17:32
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demoscene', '0011_releaser_locked'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='releaser',
            name='demoscene_r_admin_s_a0c2dc_gin',
        ),
        migrations.RemoveField(
            model_name='releaser',
            name='admin_search_document',
        ),
    ]
