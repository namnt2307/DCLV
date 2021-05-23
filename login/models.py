from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class myUser(AbstractUser):
    age = models.IntegerField(default=0)
    group_name = models.CharField(max_length=20)
    user_identifier = models.CharField(max_length=30)