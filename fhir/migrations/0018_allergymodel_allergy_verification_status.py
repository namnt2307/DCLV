# Generated by Django 3.2 on 2021-10-10 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0017_alter_allergymodel_allergy_clinical_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='allergymodel',
            name='allergy_verification_status',
            field=models.CharField(default='confirmed', max_length=100),
        ),
    ]
