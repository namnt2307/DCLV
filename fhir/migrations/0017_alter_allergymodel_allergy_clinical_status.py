# Generated by Django 3.2 on 2021-10-08 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0016_alter_conditionmodel_condition_clinical_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allergymodel',
            name='allergy_clinical_status',
            field=models.CharField(choices=[('active', 'đang hoạt động'), ('inactive', 'không hoạt động'), ('resolved', 'đã khỏi')], max_length=100),
        ),
    ]