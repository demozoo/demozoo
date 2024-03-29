# Generated by Django 1.11.8 on 2018-10-05 22:52
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pouet_id', models.IntegerField(db_index=True, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('demozoo_id', models.IntegerField(blank=True, null=True)),
                ('last_seen_at', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Production',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pouet_id', models.IntegerField(db_index=True, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('last_seen_at', models.DateTimeField()),
                ('groups', models.ManyToManyField(related_name='productions', to='pouet.Group')),
            ],
        ),
    ]
