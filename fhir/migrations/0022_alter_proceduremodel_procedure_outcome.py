# Generated by Django 3.2 on 2021-10-31 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fhir', '0021_auto_20211017_2314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proceduremodel',
            name='procedure_outcome',
            field=models.CharField(choices=[('385669000', 'Thành công'), ('385671000', 'Không thành công'), ('385670004', 'Thành công một phần')], max_length=100, null=True),
        ),
    ]
