# Generated by Django 3.2 on 2021-10-01 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0005_auto_20210930_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='encountermodel',
            name='encounter_storage',
            field=models.CharField(default='local', max_length=100),
        ),
    ]
