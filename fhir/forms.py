from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.forms import fields, widgets
from lib.tools import generate_password
from .models import EncounterModel, ServiceRequestModel, ProcedureModel, AllergyModel, UserModel, ConditionModel, ObservationModel, ProcedureModel, MedicationModel, DiagnosticReportModel

class DateInput(forms.DateInput):
    input_type = 'date'
class EHRCreationForm(forms.ModelForm):
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = get_user_model()
        fields = ('name', 'gender', 'birthdate',
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
        fields = ('identifier', 'name', 'gender', 'birthdate',
                  'home_address', 'work_address', 'telecom')


class ConditionForm(forms.ModelForm):
    

    class Meta:
        model = ConditionModel
        fields = ('condition_code', 'condition_clinicalstatus',
                  'condition_onset', 'condition_severity')
        labels = {
            'condition_code': 'Vấn đề lâm sàng',
            'condition_clinicalstatus': 'Tình trạng',
            'condition_onset': 'Dấu hiệu bắt đầu từ ngày',
            'condition_severity': 'Mức độ',
        }
        widgets = {
            'condition_onset': DateInput()
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
        model = MedicationModel
        fields = (
            'medication_medication', 'medication_reason_code', 'medication_effective', 'dosage_frequency', 'dosage_period', 'dosage_duration', 'dosage_route', 'dosage_quantity', 'dosage_when', 'dosage_offset', 'dosage_additional_instruction', 'dosage_patient_instruction'
        )
        labels = {
            'medication_medication': 'Thuốc chỉ định',
            'medication_reason_code': 'Lý do dùng thuốc',
            'medication_effective': 'Ngày bắt đầu dùng thuốc',
            'dosage_frequency': 'Tần suất dùng thuốc',
            'dosage_period': 'Chu kì dùng thuốc',
            'dosage_duration': 'Khoảng thời gian dùng thuốc',
            'dosage_route': 'Đường dùng thuốc',
            'dosage_quantity': 'Số lượng mỗi lần dùng',
            'dosage_when': 'Thời điểm dùng thuốc (thời điểm)',
            'dosage_offset': 'Thời điểm dùng thuốc (số phút từ/đến thời điểm dùng thuốc)',
            'dosage_additional_instruction': 'Hướng dẫn thêm',
            'dosage_patient_instruction': 'Hướng dẫn đặc biệt'
        }
        widgets = {
            'medication_effective': DateInput()
        }


class ServiceRequestForm(forms.ModelForm):  
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


class RequestForImageForm(forms.ModelForm):
    # CATEGORY_CHOICES = (
    #     ('363679005', 'Imaging'),
    #     ('409063005', 'Counselling'),
    #     ('409073007', 'Education'),
    #     ('387713003', 'Surgical procedure')
    # )
    class Meta:
        model = ServiceRequestModel
        fields = (
            'service_code', 'service_occurrence', 'service_note'
        )
        labels = {
            'service_code': 'Tên thủ thuật/phẫu thuật',
            'service_occurrence': 'Ngày dự kiến thực hiện',
            'service_note': 'Ghi chú thêm'
        }
        widgets = {
            'service_occurrence': DateInput(),
            # 'service_category': widgets.Select(choices=)
        }


class RequestForProcedureForm(forms.ModelForm):
    # CATEGORY_CHOICES = (
    #     ('363679005', 'Imaging'),
    #     ('409063005', 'Counselling'),
    #     ('409073007', 'Education'),
    #     ('387713003', 'Surgical procedure')
    # )
    class Meta:
        model = ServiceRequestModel
        fields = (
            'service_category','service_code', 'service_occurrence', 'service_note'
        )
        labels = {
            'service_category': 'Phân loại thủ thuật/phẫu thuật',
            'service_code': 'Tên thủ thuật/phẫu thuật',
            'service_occurrence': 'Ngày dự kiến thực hiện',
            'service_note': 'Ghi chú thêm'
        }
        widgets = {
            'service_occurrence': DateInput(),
            # 'service_category': widgets.Select(choices=)
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