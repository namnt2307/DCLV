from django.contrib import admin
from .models import PractitionerModel, ClinicalDepartment
# Register your models here.

admin.site.register(PractitionerModel)
admin.site.register(ClinicalDepartment)