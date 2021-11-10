from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

GENDER_CHOICES = (
    ('Nam','Nam'),
    ('Nữ','Nữ')
)
class myUser(AbstractUser):
    CONTACT_RELATIONSHIP_CHOICES = (
        ('C', 'Liên hệ khẩn cấp'),
        ('E', 'Chủ sở hữu lao động'),
        ('F', 'Cơ quan liên bang'),
        ('I', 'Công ty bảo hiểm'),
        ('N', 'Người nối dõi'),
        ('S', 'Cơ quan nhà nước'),
        ('U', 'Không xác định')
    )
    name = models.CharField(default='',max_length=100)
    birthdate = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3,choices=GENDER_CHOICES,default='')
    work_address = models.CharField(default= '',max_length=255)
    home_address = models.CharField(default= '',max_length=255)
    identifier = models.CharField(max_length=100, primary_key=True)
    telecom = models.CharField(default = '', max_length=10)
    group_name = models.CharField(default='',max_length=20)
    contact_relationship = models.CharField(max_length=100, null=True, blank=True, choices=CONTACT_RELATIONSHIP_CHOICES)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact_telecom = models.CharField(max_length=100, blank=True, null=True)
    contact_address = models.CharField(max_length=100, null=True, blank=True)
    contact_gender = models.CharField(max_length=100, choices=GENDER_CHOICES, null=True, blank=True)
    


