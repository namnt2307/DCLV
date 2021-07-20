from django.contrib import admin

from .models import Encounter,ServiceRequest,Procedure,Allergy,UserModel

admin.site.register(Encounter)
admin.site.register(ServiceRequest)
admin.site.register(Procedure)
admin.site.register(Allergy)
admin.site.register(UserModel)