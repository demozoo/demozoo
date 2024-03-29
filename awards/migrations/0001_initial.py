# Generated by Django 1.11.27 on 2020-01-31 00:45
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('eligibility_start_date', models.DateField(help_text='Earliest release date a production can have to be considered for these awards')),
                ('eligibility_end_date', models.DateField(help_text='Latest release date a production can have to be considered for these awards')),
                ('recommendations_enabled', models.BooleanField(default=False, help_text='Whether these awards are currently accepting recommendations')),
                ('reporting_enabled', models.BooleanField(default=False, help_text='Whether jurors can currently view reports for these awards')),
            ],
        ),
        migrations.AddField(
            model_name='category',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='awards.Event'),
        ),
    ]
