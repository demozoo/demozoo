# Generated by Django 4.0.8 on 2023-01-05 23:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pouet', '0006_platform_productiontype_production_platforms_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetitionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pouet_id', models.IntegerField(db_index=True, unique=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pouet_id', models.IntegerField(db_index=True, unique=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='CompetitionPlacing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField()),
                ('competition_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='pouet.competitiontype')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competition_placings', to='pouet.party')),
                ('production', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competition_placings', to='pouet.production')),
            ],
        ),
    ]
