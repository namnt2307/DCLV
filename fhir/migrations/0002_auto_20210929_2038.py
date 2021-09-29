# Generated by Django 3.2 on 2021-09-29 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conditionmodel',
            name='condition_version',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='diagnosticreportmodel',
            name='diagnostic_version',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='medicationmodel',
            name='medication_version',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='observationmodel',
            name='observation_version',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='proceduremodel',
            name='procedure_version',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='servicerequestmodel',
            name='service_version',
            field=models.IntegerField(null=True),
        ),
    ]