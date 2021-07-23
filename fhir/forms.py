from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.forms import fields
from lib.tools import generate_password
from .models import EncounterModel, ServiceRequestModel, ProcedureModel, AllergyModel, UserModel, ConditionModel

class EHRCreationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('full_name', 'gender', 'birth_date',
                  'home_address', 'work_address', 'user_identifier', 'telecom')

class EncounterForm(forms.ModelForm):
    class Meta:
        model = EncounterModel
        fields = ('class_select', 'type_select',
         'service_type', 'priority', 'reason_code', 'location')
        labels = {
            'class_select': 'Loại hình thăm khám',
            'type_select': 'Loại bệnh án',
            'service_type': 'Dịch vụ khám bệnh',
            'priority': 'Mức độ ưu tiên',
            'reason_code': 'Lý do đến khám',
            'location': 'Khoa khám bệnh'
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = UserModel()
        fields = ('user_identifier', 'full_name', 'gender', 'birth_date', 'home_address', 'work_address', 'telecom')

class ConditionForm(forms.ModelForm):
    class Meta:
        model = ConditionModel
        fields = ('code','clinicalStatus','onset','severity', 'self_history','allergy','family_history')
        labels = {
            'code': 'Vấn đề lâm sàng',
            'clinicalStatus': 'Tình trạng',
            'onset': 'Dấu hiệu bắt đầu từ ngày',
            'severity': 'Mức độ',
            'self_history': 'Tiền sử bệnh',
            'allergy': 'Dị ứng',
            'family_history': 'Tiền sử bệnh gia đình'
        }
        