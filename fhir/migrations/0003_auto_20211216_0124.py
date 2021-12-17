# Generated by Django 3.2 on 2021-12-15 18:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0001_initial'),
        ('fhir', '0002_alter_encountermodel_encounter_class'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schedule',
            name='practitioner_location',
        ),
        migrations.AddField(
            model_name='schedule',
            name='practitioner_department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.clinicaldepartment'),
        ),
    ]