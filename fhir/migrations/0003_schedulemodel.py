# Generated by Django 3.2 on 2021-11-20 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0002_auto_20211117_2127'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('practitioner_name', models.CharField(max_length=100)),
                ('practitioner_identifier', models.CharField(max_length=20)),
                ('practitioner_location', models.CharField(max_length=100, null=True)),
                ('schedule_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
            ],
        ),
    ]
