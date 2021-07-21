from django.db import models
# Create your models here.
from login.models import myUser
from datetime import datetime


class Encounter(models.Model):
    user_identifier = models.ForeignKey(myUser, on_delete=models.CASCADE)
    encounter_id = models.IntegerField(unique=True)
    start_date = models.DateTimeField(default=datetime.now)


class Observation(models.Model):
    encounter_id = models.OneToOneField(Encounter, on_delete=models.CASCADE)
    body_weight = models.IntegerField(default=0)
    respiratory_rate = models.IntegerField(default=0)
    diastolic_blood_pressure = models.IntegerField(default=0)
    systolic_blood_pressure = models.IntegerField(default=0)
    body_temperature = models.IntegerField(default=0)
    heart_rate = models.IntegerField(default=0)
