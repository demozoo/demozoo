# Generated by Django 2.2.17 on 2021-01-10 19:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('demoscene', '0017_membership_group_limit_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='releaser',
            name='woe_id',
        ),
    ]