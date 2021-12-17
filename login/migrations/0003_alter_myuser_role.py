# Generated by Django 3.2 on 2021-12-12 04:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0002_alter_myuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='role',
            field=models.CharField(choices=[('admin', 'admin'), ('patient', 'Bệnh nhân'), ('doctor', 'Bác sĩ'), ('surgeon', 'Bác sĩ phẫu thuật'), ('medical assistant', 'Trợ lý y tế'), ('medical laboratory technician', 'Kỹ thuật viên phòng thí nghiệm y tế'), ('diagnostic imaging technician', 'Kỹ thuật viên chẩn đoán hình ảnh'), ('nurse', 'Y tá')], default='patient', max_length=100),
        ),
    ]
