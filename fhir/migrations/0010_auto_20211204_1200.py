# Generated by Django 3.2 on 2021-12-04 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0009_rename_planned_encounter_assignedencounter_assigned_encounter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Medicine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicine_name', models.CharField(max_length=200, unique=True)),
                ('medicine_unit', models.CharField(max_length=50, null=True)),
                ('medicine_price_on_unit', models.IntegerField(null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='conditionmodel',
            name='condition_code',
            field=models.CharField(default='', max_length=1000),
        ),
    ]