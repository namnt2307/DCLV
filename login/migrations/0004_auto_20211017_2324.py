# Generated by Django 3.2 on 2021-10-17 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0003_auto_20210927_2030'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='contact_address',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='myuser',
            name='contact_gender',
            field=models.CharField(blank=True, choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='myuser',
            name='contact_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='myuser',
            name='contact_relationship',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='myuser',
            name='contact_telecom',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
