from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

GENDER_CHOICES = (
    ('Nam','Nam'),
    ('Nữ','Nữ')
)
class myUser(AbstractUser):
    name = models.CharField(default='',max_length=100)
    birthdate = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3,choices=GENDER_CHOICES,default='')
    work_address = models.CharField(default= '',max_length=255)
    home_address = models.CharField(default= '',max_length=255)
    identifier = models.CharField(max_length=100, primary_key=True)
    telecom = models.CharField(default = '', max_length=10)
    group_name = models.CharField(default='',max_length=20)
    


