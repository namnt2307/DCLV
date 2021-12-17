from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.forms import fields, widgets
from lib.tools import generate_password
from .models import EncounterModel, ServiceRequestModel, ProcedureModel, AllergyModel, PatientModel, ConditionModel, ObservationModel, ProcedureModel, MedicationModel, DiagnosticReportModel

class DateInput(forms.DateInput):
    input_type = 'date'
# class EHRCreationForm(forms.ModelForm):
#     birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

#     class Meta:
#         model = get_user_model()
#         fields = ('name', 'gender', 'birthdate',
#                   'home_address', 'work_address', 'identifier', 'telecom', 'contact_name', 'contact_gender', 'contact_relationship', 'contact_address', 'contact_telecom')


class EncounterForm(forms.ModelForm):
    class Meta:
        model = EncounterModel
        fields = ('encounter_class', 'encounter_type', 'encounter_location',
                  'encounter_service', 'encounter_priority', 'encounter_reason')
        labels = {
            'encounter_class': 'Loại hình thăm khám',
            'encounter_type': 'Loại bệnh án',
            'encounter_location': 'Khoa Khám bệnh',
            'encounter_service': 'Dịch vụ khám bệnh',
            'encounter_priority': 'Mức độ ưu tiên',
            'encounter_reason': 'Lý do đến khám',
        }


class PatientForm(forms.ModelForm):
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = PatientModel
        fields = ('identifier', 'name', 'gender', 'birthdate',
                  'home_address', 'work_address', 'telecom', 'contact_name', 'contact_gender', 'contact_relationship', 'contact_address', 'contact_telecom')


class ConditionForm(forms.ModelForm):
    class Meta:
        model = ConditionModel
        fields = ('condition_code', 'condition_clinical_status',
                  'condition_onset',  'condition_abatement','condition_severity')
        labels = {
            'condition_code': 'Vấn đề lâm sàng',
            'condition_clinical_status': 'Tình trạng',
            'condition_onset': 'Dấu hiệu bắt đầu từ ngày',
            'condition_severity': 'Mức độ',
        }
        widgets = {
            'condition_onset': DateInput(),
            'condition_abatement': DateInput()
        }


class ObservationForm(forms.ModelForm):
    class Meta:
        model = ObservationModel
        fields = (
            ('observation_value_quantity', 'observation_note')
        )
        labels = {
            'observation_note': 'Nhận xét của bác sĩ'
        }


class ProcedureForm(forms.ModelForm):
    class Meta:
        model = ProcedureModel
        fields = (
            'procedure_category', 'procedure_code', 'procedure_location', 'procedure_reason_code'
        )
        labels = {
            'procedure_category': 'Phân loại phương pháp điều trị',
            'procedure_code': 'Phương pháp thực hiện',
            'procedure_location': 'Nơi thực hiện',
            'procedure_reason_code': 'Lý do thực hiện'
        }


class ProcedureDetailForm(forms.ModelForm):
    class Meta:
        model = ProcedureModel
        fields = (
            'procedure_outcome', 'procedure_complication', 'procedure_follow_up', 'procedure_used', 'procedure_note'
        )
        labels = {
            'procedure_outcome': 'Kết quả thủ thuật, phẫu thuật',
            'procedure_complication': 'Các biến chứng sau thủ thuật, phẫu thuật',
            'procedure_follow_up': 'Các hướng dẫn bệnh nhân sau thủ thuật, phẫu thuật',
            'procedure_used': 'Thiết bị sử dụng',
            'procedure_note': 'Ghi chú của bác sĩ'
        }


class MedicationForm(forms.ModelForm):

    class Meta:
        DOSAGE_WHEN_CHOICES = (
        ('HS', 'dùng trước khi đi ngủ'),
        ('WAKE', 'dùng sau khi thức dậy'),
        ('C', 'dùng trong bữa ăn'),
        ('CM', 'dùng trong bữa sáng'),
        ('CD', 'dùng trong bữa trưa'),
        ('CV', 'dùng trong bữa tối'),
        ('AC', 'dùng trước bữa ăn'),
        ('ACM', 'dùng trước bữa sáng'),
        ('ACD', 'dùng trước bữa trưa'),
        ('ACV', 'dùng trước bữa tối'),
        ('PC', 'dùng sau bữa ăn'),
        ('PCM', 'dùng sau bữa sáng'),
        ('PCD', 'dùng sau bữa trưa'),
        ('PCV', 'dùng sau bữa tối')
        )
        model = MedicationModel
        fields = (
            'medication_medication', 'medication_reason_code', 'dosage_frequency', 'dosage_period', 'dosage_period_unit', 'dosage_duration', 'dosage_duration_unit', 'dosage_route', 'dosage_quantity', 'dosage_quantity_unit','dosage_when', 'dosage_offset', 'dosage_additional_instruction', 'dosage_patient_instruction'
        )
        labels = {
            'medication_medication': 'Thuốc chỉ định',
            'medication_reason_code': 'Lý do dùng thuốc',
            'dosage_frequency': 'Tần suất dùng thuốc',
            'dosage_period': 'Chu kì dùng thuốc',
            'dosage_period_unit': '',
            'dosage_duration': 'Khoảng thời gian dùng thuốc',
            'dosage_duration_unit': '',
            'dosage_route': 'Đường dùng thuốc',
            'dosage_quantity': 'Số lượng mỗi lần dùng',
            'dosage_quantity_unit': '',
            'dosage_when': 'Thời điểm dùng thuốc (thời điểm)',
            'dosage_offset': 'Thời điểm dùng thuốc (số phút từ/đến thời điểm dùng thuốc)',
            'dosage_additional_instruction': 'Hướng dẫn thêm',
            'dosage_patient_instruction': 'Hướng dẫn đặc biệt'
        }
        widgets = {
            'medication_effective': DateInput(),
            'dosage_when': forms.Select(choices=DOSAGE_WHEN_CHOICES ,attrs={'onchange':'whenFunction();'})
        }


class ServiceRequestForm(forms.ModelForm):  
    service_occurrence = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = ServiceRequestModel
        fields = (
            'service_code', 'service_occurrence', 'service_note'
        )
        labels = {
            'service_code': 'Tên xét nghiệm',
            'service_occurrence': 'Ngày dự kiến thực hiện',
            'service_note': 'Ghi chú thêm'
        }
        widgets = {
            'service_occurrence': DateInput()
        }


class DiagnosticReportForm(forms.ModelForm):
    class Meta:
        model = DiagnosticReportModel
        fields = (
            'diagnostic_conclusion',
        ) 
        labels = {
            'diagnostic_conclusion': 'Chẩn đoán của bác sĩ'
        }
        widgets = {
            'diagnostic_conclusion': forms.Textarea()
        }

class AllergyForm(forms.ModelForm):
    class Meta:
        model = AllergyModel
        fields = (
            'allergy_clinical_status', 'allergy_category', 'allergy_code', 'allergy_criticality', 'allergy_onset', 'allergy_last_occurrence', 'allergy_reaction_substance', 'allergy_reaction_manifestation', 'allergy_reaction_severity'
        )
        labels = {
            'allergy_clinical_status': 'tình trạng dị ứng',
            'allergy_category': 'phân loại dị ứng',
            'allergy_code': 'dị ứng',
            'allergy_criticality': 'mức độ nghiêm trọng',
            'allergy_onset': 'thời điểm phát hiện',
            'allergy_last_occurrence': 'thời điểm tái phát gần nhất',
            'allergy_reaction_substance': 'thành phần dị ứng',
            'allergy_reaction_manifestation': 'phản ứng',
            'allergy_reaction_severity': 'mức độ phản ứng'
        }
        widgets = {
            'allergy_onset': DateInput(),
            'allergy_last_occurrence': DateInput()
        }