from django.contrib import admin

from .models import EncounterModel,ServiceRequestModel,ProcedureModel,AllergyModel,UserModel,ConditionModel, ObservationModel

admin.site.register(EncounterModel)
admin.site.register(ServiceRequestModel)
admin.site.register(ProcedureModel)
admin.site.register(AllergyModel)
admin.site.register(UserModel)
admin.site.register(ConditionModel)
admin.site.register(ObservationModel)