# Generated by Django 1.9.7 on 2017-02-22 21:02
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exclusion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_id', models.IntegerField()),
                ('report_name', models.CharField(max_length=255)),
            ],
        ),
    ]
