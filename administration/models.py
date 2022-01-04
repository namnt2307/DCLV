from django.db import models
from datetime import datetime
# Create your models here.

class ClinicalDepartment(models.Model):
    DEPARTMENT_CHOICES = (
        ('lâm sàng', 'Lâm sàng'),
        ('cận lâm sàng', 'Cận lâm sàng')
    )
    department_name = models.CharField(max_length=100, primary_key=True)
    department_category = models.CharField(max_length=100)
    department_type = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='lâm sàng')
    def __str__(self):
        return f"{self.department_name}"

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
        ('diagnostic imaging technician', 'Kỹ thuật viên chẩn đoán hình ảnh'),
        ('nurse', 'Y tá'),
    )
    identifier = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=100)
    birthdate = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3, choices=GENDER_CHOICES)
    home_address = models.CharField(max_length=255)
    telecom = models.CharField(max_length=10)
    department = models.ForeignKey(ClinicalDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    practitioner_role = models.CharField(max_length=100, choices=PRACTITIONER_ROLE_CHOICES, default='doctor')
    qualification = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name}"
    


    


