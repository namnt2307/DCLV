from django.db import models
from datetime import datetime
# Create your models here.

class PractitionerModel(models.Model):
    GENDER_CHOICES = (
        ('Nam', 'Nam'),
        ('Nữ', 'Nữ')
    )
    PRACTITIONER_ROLE_CHOICES = (
        ('doctor', 'Bác sĩ'),
        ('surgeon', 'Bác sĩ phẫu thuật'),
        ('medical assistant', 'Trợ lý y tế'),
        ('medical laboratory technician', 'Kỹ thuật viên phòng thí nghiệm y tế'),
        ('X-ray technician', 'Kỹ thuật viên X-quang'),
        ('ultrasound technician', 'Kỹ thuật viên siêu âm'),
        ('nurse', 'Y tá'),
    )
    identifier = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=100)
    birthdate = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3, choices=GENDER_CHOICES)
    home_address = models.CharField(max_length=255)
    telecom = models.CharField(max_length=10)
    practitioner_role = models.CharField(max_length=100, choices=PRACTITIONER_ROLE_CHOICES, default='doctor')
    qualification = models.CharField(max_length=100)
    


