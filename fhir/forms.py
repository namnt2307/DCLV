from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.forms import fields
from lib.tools import generate_password
from .models import EncounterModel, ServiceRequestModel, ProcedureModel, AllergyModel, UserModel, ConditionModel, ObservationModel, ProcedureModel

class EHRCreationForm(forms.ModelForm):
    birthDate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
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
    condition_onset=forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
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


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = ProcedureModel
        fields = (
            'procedure_category', 'procedure_code', 'procedure_location', 'procedure_reasonCode'
        )
        labels = {
            'procedure_category': 'Phân loại phương pháp điều trị',
            'procedure_code': 'Phương pháp thực hiện',
            'procedure_location': 'Nơi thực hiện',
            'procedure_reasonCode': 'Lý do thực hiện'
        }


class ProcedureDetailForm(forms.ModelForm):
    class Meta:
        model = ProcedureModel
        fields = (
            'procedure_outcome', 'procedure_complication', 'procedure_followUp', 'procedure_focalDevice', 'procedure_note'
        )
        labels = {
            'procedure_outcome': 'Kết quả thủ thuật, phẫu thuật',
            'procedure_complication': 'Các biến chứng sau thủ thuật, phẫu thuật',
            'procedure_followUp': 'Các hướng dẫn bệnh nhân sau thủ thuật, phẫu thuật',
            'procedure_focalDevice': 'Thiết bị thực hiện thủ thuật, phẫu thuật',
            'procedure_note': 'Ghi chú của bác sĩ'
        }