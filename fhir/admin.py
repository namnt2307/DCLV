from django.contrib import admin

from .models import EncounterModel,ServiceRequestModel,ProcedureModel,AllergyModel,PatientModel,ConditionModel, ObservationModel, MedicationModel, DiagnosticReportModel,DischargeDiseases, ComorbidityDiseases, ScheduleModel

admin.site.register(EncounterModel)
admin.site.register(ServiceRequestModel)
admin.site.register(ProcedureModel)
admin.site.register(AllergyModel)
admin.site.register(PatientModel)
admin.site.register(ConditionModel)
admin.site.register(ObservationModel)
admin.site.register(MedicationModel)
admin.site.register(DiagnosticReportModel)
admin.site.register(DischargeDiseases)
admin.site.register(ComorbidityDiseases)
admin.site.register(ScheduleModel)