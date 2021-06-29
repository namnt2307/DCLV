from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

GENDER_CHOICES = (
    ('nam','Nam'),
    ('nu','Nu')
)
class myUser(AbstractUser):
    full_name = models.CharField(default='',max_length=100)
    birth_date = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3,choices=GENDER_CHOICES,default='')
    work_address = models.CharField(default= '',max_length=255)
    home_address = models.CharField(default= '',max_length=255)
    user_identifier = models.CharField(default = '',max_length=30,unique=True)
    group_name = models.CharField(default='',max_length=20)
    health_exam_status = models.BooleanField(default=False)

