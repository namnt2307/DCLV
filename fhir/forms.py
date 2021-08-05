from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.forms import fields
from lib.tools import generate_password
from .models import EncounterModel, ServiceRequestModel, ProcedureModel, AllergyModel, UserModel, ConditionModel, ObservationModel

class EHRCreationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('name', 'gender', 'birthDate',
                  'home_address', 'work_address', 'identifier', 'telecom')

class EncounterForm(forms.ModelForm):
    class Meta:
        model = EncounterModel
        fields = ('encounter_class', 'encounter_type',
         'encounter_service', 'encounter_priority', 'encounter_reason')
        labels = {
            'encounter_class': 'Loại hình thăm khám',
            'encounter_type': 'Loại bệnh án',
            'encounter_service': 'Dịch vụ khám bệnh',
            'encounter_priority': 'Mức độ ưu tiên',
            'encounter_reason': 'Lý do đến khám',
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = UserModel()
        fields = ('identifier', 'name', 'gender', 'birthDate', 'home_address', 'work_address', 'telecom')

class ConditionForm(forms.ModelForm):
    class Meta:
        model = ConditionModel
        fields = ('condition_code','condition_clinicalstatus','condition_onset','condition_severity')
        labels = {
            'condition_code': 'Vấn đề lâm sàng',
            'condition_clinicalstatus': 'Tình trạng',
            'condition_onset': 'Dấu hiệu bắt đầu từ ngày',
            'condition_severity': 'Mức độ',
        }
        
class ObservationForm(forms.ModelForm):
    class Meta:
        model = ObservationModel
        fields = (
            ('observation_valuequantity','observation_note')
        )
        labels = {
            'observation_note': 'Nhận xét của bác sĩ'
        }