from django.db import models
from django.db.models.enums import Choices
# Create your models here.
from login.models import myUser
from datetime import datetime

class EncounterModel(models.Model):
    CLASS_CHOICES = (
        ('IMP', 'Nội trú'),
        ('AMB', 'Ambulatory'),
        ('FLD', 'Khám tại địa điểm ngoài'),
        ('EMER', 'Khẩn cấp'),
        ('HH', 'Khám tại nhà'),
        ('ACUTE', 'Nội trú khẩn cấp'),
        ('NONAC', 'Nội trú không khẩn cấp'),
        ('OBSENC', 'Thăm khám quan sát'),
        ('SS', 'Ngoại trú'),
        ('VR', 'Trực tuyến'),
        ('PRENC', 'Tái khám')
    )
    TYPE_CHOICES = (
        ('1', 'Bệnh án nội khoa'),
        ('2', 'Bệnh án ngoại khoa'),
        ('3', 'Bệnh án phụ khoa'),
        ('4', 'Bệnh án sản khoa')
    )
    PRIORITY_CHOICES = (
        ('A', 'ASAP'),
        ('EL', 'Tự chọn'),
        ('EM', 'Khẩn cấp'),
        ('P', 'Trước'),
        ('R', 'Bình thường'),
        ('S', 'Star')
    )
    LOCATION_CHOICES = (
        ('1', 'Khoa Khám bệnh'),
        ('2', 'Khoa Hồi sức cấp cứu'),
        ('3', 'Khoa Nội tổng hợp'),
        ('4', 'Khoa Nội tổng hợp'),
        ('5', 'Khoa Nội tiêu hóa'),
        ('6', 'Khoa Nội - tiết niệu'),
        ('7', 'Khoa Nội tiết'),
        ('8', 'Khoa Nội cơ - xương - khớp'),
        ('9', 'Khoa Nội tiết'),
        ('10', 'Khoa Dị ứng'),
        ('11', 'Khoa Huyết học lâm sàng'),
        ('12', 'Khoa Truyền nhiễm'),
        ('13', 'Khoa Lao'),
        ('14', 'Khoa Tâm thần'),
        ('15', 'Khoa Thần kinh')
    )
    user_identifier = models.ForeignKey(myUser,on_delete=models.CASCADE)
    encounter_identifier = models.CharField(max_length=100, primary_key=True)
    encounter_start = models.DateTimeField(default=datetime.now)
    encounter_end = models.DateTimeField(null=True)
    encounter_status = models.CharField(max_length=20, default='in-progress')
    encounter_class = models.CharField(null=True,max_length=10,choices=CLASS_CHOICES)
    encounter_type = models.CharField(null=True,max_length=30, choices=TYPE_CHOICES)
    encounter_service = models.CharField(null=True,max_length=20)
    encounter_priority = models.CharField(null=True,max_length=10, choices=PRIORITY_CHOICES)
    encounter_reason = models.CharField(null=True,max_length=10)
    encounter_location = models.CharField(null=True,max_length=20, choices=LOCATION_CHOICES)
    encounter_submitted = models.BooleanField(default=False)


class UserModel(models.Model):
    GENDER_CHOICES = (
    ('Nam','Nam'),
    ('Nữ','Nữ')
    )
    user_identifier = models.CharField(primary_key=True, max_length=10)
    full_name = models.CharField(default='',max_length=100)
    birth_date = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3,choices=GENDER_CHOICES,default='')
    work_address = models.CharField(default= '',max_length=255)
    home_address = models.CharField(default= '',max_length=255)
    telecom = models.CharField(default = '', max_length=10)
    group_name = models.CharField(default='',max_length=20)   

class ConditionModel(models.Model):
    CLINICAL_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Recurrence', 'Recurrence'),
        ('Relapse', 'Relapse'),
        ('Remission', 'Remission'),
        ('Resolved', 'Resolves')
    )
    SEVERITY_CHOICES = (
        ('24484000', 'Nặng'),
        ('6736007', 'Vừa'),
        ('255604002', 'Nhẹ')
    )
    encounter_identifier = models.ForeignKey(EncounterModel, on_delete=models.CASCADE)
    condition_identifier = models.CharField(max_length=100, primary_key=True)
    condition_code = models.CharField(max_length=100, default='')
    condition_clinicalstatus = models.CharField(max_length=100, choices=CLINICAL_CHOICES)
    condition_onset = models.DateTimeField(default='')
    condition_severity = models.CharField(choices=SEVERITY_CHOICES,max_length=100)

class ServiceRequestModel(models.Model):
    encounter_identifier = models.ForeignKey(EncounterModel, on_delete=models.CASCADE)
    service_identifier = models.CharField(max_length=100, primary_key=True)
    service_status = models.CharField(default='active', max_length=100)
    service_category = models.CharField(max_length=10)
    service_location = models.CharField(max_length = 100)
    service_note = models.TextField(null=True)
    service_code = models.TextField(null=True)

class ObservationModel(models.Model):
    encounter_identifier = models.ForeignKey(EncounterModel,on_delete=models.CASCADE)
    service_identifier = models.CharField(max_length=100, default='')
    observation_identifier = models.CharField(max_length=100, primary_key=True)
    observation_status = models.CharField(default='registered',max_length=10)
    observation_name  = models.CharField(default='',max_length=100)
    observation_category = models.CharField(default='',max_length=10)
    observation_effective = models.DateTimeField(default=datetime.now)
    observation_valuequantity = models.CharField(default='',max_length=10,null=True)
    observation_valueunit = models.CharField(default='',max_length = 10)
    observation_performer = models.CharField(default='',max_length=100)
    observation_note = models.CharField(default='', max_length=300,null=True)

class ProcedureModel(models.Model):
    encounter_identifier = models.ForeignKey(EncounterModel,on_delete=models.CASCADE)
    procedure_status = models.CharField(max_length=100)
    procedure_category = models.CharField(max_length=100)
    procedure_code = models.CharField(max_length=100)
    procedure_location = models.CharField(max_length=100)
    procedure_outcome = models.CharField(max_length=100)

class AllergyModel(models.Model):
    patient_id = models.ForeignKey(myUser,on_delete=models.CASCADE)
    allergy_status = models.CharField(max_length=100)
    allergy_type = models.CharField(max_length=100)
    allergy_category = models.CharField(max_length=100)
    allergy_code = models.CharField(max_length=100)
    allergy_criticality = models.CharField(max_length=100)

class MedicineModel(models.Model):
    encounter_identifier = models.ForeignKey(EncounterModel,on_delete=models.CASCADE)
    medication = models.CharField(max_length=100)
    effective = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    