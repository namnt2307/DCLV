from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

class myUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'admin'),
        ('patient', 'Bệnh nhân'),
        ('doctor', 'Bác sĩ'),
        ('surgeon', 'Bác sĩ phẫu thuật'),
        ('medical assistant', 'Trợ lý y tế'),
        ('medical laboratory technician', 'Kỹ thuật viên phòng thí nghiệm y tế'),
        ('X-ray technician', 'Kỹ thuật viên X-quang'),
        ('ultrasound technician', 'Kỹ thuật viên siêu âm'),
        ('nurse', 'Y tá')
    )
    # name = models.CharField(default='',max_length=100)
    # birthdate = models.DateField(default=datetime.now)
    # gender = models.CharField(max_length=3,choices=GENDER_CHOICES,default='')
    # work_address = models.CharField(default= '',max_length=255)
    # home_address = models.CharField(default= '',max_length=255)
    # identifier = models.CharField(max_length=100, primary_key=True)
    # telecom = models.CharField(default = '', max_length=10)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='patient')
    


    
    


