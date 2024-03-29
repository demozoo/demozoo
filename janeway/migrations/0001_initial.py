# Generated by Django 1.11.8 on 2019-01-27 21:11
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('janeway_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('real_name', models.CharField(blank=True, max_length=255)),
                ('real_name_hidden', models.BooleanField(default=False)),
                ('is_group', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('since', models.DateField(blank=True, null=True)),
                ('until', models.DateField(blank=True, null=True)),
                ('founder', models.BooleanField(default=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_memberships', to='janeway.Author')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to='janeway.Author')),
            ],
        ),
        migrations.CreateModel(
            name='Name',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('janeway_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('abbreviation', models.CharField(blank=True, max_length=255)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='names', to='janeway.Author')),
            ],
        ),
    ]
