from django.contrib import admin

from .models import EncounterModel,ServiceRequestModel,ProcedureModel,AllergyModel,PatientModel,ConditionModel, ObservationModel, MedicationModel, DiagnosticReportModel,DischargeDisease, ComorbidityDisease, Schedule, AssignedEncounter, Medicine

admin.site.register(EncounterModel)
admin.site.register(ServiceRequestModel)
admin.site.register(ProcedureModel)
admin.site.register(AllergyModel)
admin.site.register(PatientModel)
admin.site.register(ConditionModel)
admin.site.register(ObservationModel)
admin.site.register(MedicationModel)
admin.site.register(DiagnosticReportModel)
admin.site.register(DischargeDisease)
admin.site.register(ComorbidityDisease)
admin.site.register(Schedule)
admin.site.register(AssignedEncounter)
admin.site.register(Medicine)