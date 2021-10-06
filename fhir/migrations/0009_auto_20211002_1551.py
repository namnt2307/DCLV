# Generated by Django 3.2 on 2021-10-02 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0008_remove_encountermodel_encounter_submitted'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicationmodel',
            name='dosage_duration_unit',
            field=models.CharField(choices=[('s', 'giây'), ('min', 'phút'), ('h', 'giờ'), ('d', 'ngày'), ('wk', 'tuần'), ('mo', 'tháng'), ('a', 'năm')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='medicationmodel',
            name='dosage_period_unit',
            field=models.CharField(choices=[('s', 'giây'), ('min', 'phút'), ('h', 'giờ'), ('d', 'ngày'), ('wk', 'tuần'), ('mo', 'tháng'), ('a', 'năm')], max_length=100, null=True),
        ),
    ]
