# Generated by Django 3.2 on 2021-11-22 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0004_schedulemodel_session'),
    ]

    operations = [
        migrations.AlterField(
            model_name='encountermodel',
            name='encounter_status',
            field=models.CharField(default='queued', max_length=20),
        ),
    ]