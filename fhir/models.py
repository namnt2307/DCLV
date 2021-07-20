from django.db import models
# Create your models here.
from login.models import myUser
from datetime import datetime

class Encounter(models.Model):
    user_identifier = models.ForeignKey(myUser,on_delete=models.CASCADE)
    encounter_id = models.IntegerField(default=0,primary_key=True)
    start_date = models.DateTimeField(default=datetime.now)
    end_date = models.DateTimeField(null=True)
    class_select = models.CharField(default='',max_length=10)
    type_select = models.CharField(default='',max_length=30)
    service_type = models.CharField(default='',max_length=20)
    priority = models.CharField(default='',max_length=10)
    reason_code = models.CharField(default='',max_length=10)
    location = models.CharField(default='',max_length=20)

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

class Condition(models.Model):
    encounter_id = models.ForeignKey(Encounter, on_delete=models.CASCADE)
    clinicalStatus = models.CharField(max_length=100)
    onset = models.DateTimeField()
    severity = models.CharField(max_length=100)
    self_history = models.CharField(max_length=100)
    allergy = models.CharField(max_length=100)
    family_history = models.CharField(max_length=100)

class ServiceRequest(models.Model):
    encounter_id = models.ForeignKey(Encounter, on_delete=models.CASCADE)
    servicerequest_id = models.CharField(max_length=20)
    request_status = models.CharField(max_length=100)
    request_type = models.CharField(max_length=10)
    request_location = models.CharField(max_length = 100)
    request_note = models.TextField()
    request_description = models.TextField()

class Observation(models.Model):
    service_id = models.ForeignKey(ServiceRequest,on_delete=models.CASCADE)
    status = models.CharField(default='',max_length=10)
    category = models.CharField(default='',max_length=10)
    effective = models.DateTimeField(default=datetime.now)
    valuequantity = models.CharField(default='',max_length=10)
    valueunit = models.CharField(default='',max_length = 10)
    performer = models.CharField(default='',max_length=100)

class Procedure(models.Model):
    encounter_id = models.ForeignKey(Encounter,on_delete=models.CASCADE)
    procedure_status = models.CharField(max_length=100)
    procedure_category = models.CharField(max_length=100)
    procedure_code = models.CharField(max_length=100)
    procedure_location = models.CharField(max_length=100)
    procedure_outcome = models.CharField(max_length=100)

class Allergy(models.Model):
    patient_id = models.ForeignKey(myUser,on_delete=models.CASCADE)
    allergy_status = models.CharField(max_length=100)
    allergy_type = models.CharField(max_length=100)
    allergy_category = models.CharField(max_length=100)
    allergy_code = models.CharField(max_length=100)
    allergy_criticality = models.CharField(max_length=100)

class Medicine(models.Model):
    encounter_id = models.ForeignKey(Encounter,on_delete=models.CASCADE)
    medication = models.CharField(max_length=100)
    effective = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    