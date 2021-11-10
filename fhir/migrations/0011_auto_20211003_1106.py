# Generated by Django 3.2 on 2021-10-03 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0010_auto_20211003_1100'),
    ]

    operations = [
        migrations.AddField(
            model_name='encountermodel',
            name='encounter_version',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='conditionmodel',
            name='condition_version',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='observationmodel',
            name='observation_version',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='proceduremodel',
            name='procedure_version',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='servicerequestmodel',
            name='service_version',
            field=models.IntegerField(default=0),
        ),
    ]