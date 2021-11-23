from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.enums import Choices
# Create your models here.
from login.models import myUser
from datetime import datetime





class PatientModel(models.Model):
    GENDER_CHOICES = (
        ('Nam', 'Nam'),
        ('Nữ', 'Nữ')
    )
    CONTACT_RELATIONSHIP_CHOICES = (
        ('C', 'Liên hệ khẩn cấp'),
        ('E', 'Chủ sở hữu lao động'),
        ('F', 'Cơ quan liên bang'),
        ('I', 'Công ty bảo hiểm'),
        ('N', 'Người nối dõi'),
        ('S', 'Cơ quan nhà nước'),
        ('U', 'Không xác định')
    )
    identifier = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(default='', max_length=100)
    birthdate = models.DateField(default=datetime.now)
    gender = models.CharField(max_length=3, choices=GENDER_CHOICES, default='')
    work_address = models.CharField(default='', max_length=255)
    home_address = models.CharField(default='', max_length=255)
    telecom = models.CharField(default='', max_length=10)
    group_name = models.CharField(default='patient', max_length=20)
    contact_relationship = models.CharField(max_length=100, null=True, blank=True, default='C', choices=CONTACT_RELATIONSHIP_CHOICES)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact_telecom = models.CharField(max_length=100, blank=True, null=True)
    contact_address = models.CharField(max_length=100, null=True, blank=True)
    contact_gender = models.CharField(max_length=100, choices=GENDER_CHOICES, null=True, blank=True)

class EncounterModel(models.Model):
    CLASS_CHOICES = (
        ('IMP', 'Nội trú'),
        ('AMB', 'Ngoại trú'),
        ('FLD', 'Khám tại địa điểm ngoài'),
        ('EMER', 'Khẩn cấp'),
        ('HH', 'Khám tại nhà'),
        ('ACUTE', 'Nội trú khẩn cấp'),
        ('NONAC', 'Nội trú không khẩn cấp'),
        ('OBSENC', 'Thăm khám quan sát'),
        ('SS', 'Thăm khám trong ngày'),
        ('VR', 'Trực tuyến'),
        ('PRENC', 'Tái khám')
    )
    TYPE_CHOICES = (
        ('Bệnh án nội khoa', 'Bệnh án nội khoa'),
        ('Bệnh án ngoại khoa', 'Bệnh án ngoại khoa'),
        ('Bệnh án phụ khoa', 'Bệnh án phụ khoa'),
        ('Bệnh án sản khoa', 'Bệnh án sản khoa')
    )
    PRIORITY_CHOICES = (
        ('A', 'ASAP'),
        ('EL', 'Tự chọn'),
        ('EM', 'Khẩn cấp'),
        ('P', 'Trước'),
        ('R', 'Bình thường'),
        ('S', 'Star')
    )
    # LOCATION_CHOICES = (
    #     ('1', 'Khoa Khám bệnh'),
    #     ('2', 'Khoa Hồi sức cấp cứu'),
    #     ('3', 'Khoa Nội tổng hợp'),
    #     ('4', 'Khoa Nội tổng hợp'),
    #     ('5', 'Khoa Nội tiêu hóa'),
    #     ('6', 'Khoa Nội - tiết niệu'),
    #     ('7', 'Khoa Nội tiết'),
    #     ('8', 'Khoa Nội cơ - xương - khớp'),
    #     ('9', 'Khoa Nội tiết'),
    #     ('10', 'Khoa Dị ứng'),
    #     ('11', 'Khoa Huyết học lâm sàng'),
    #     ('12', 'Khoa Truyền nhiễm'),
    #     ('13', 'Khoa Lao'),
    #     ('14', 'Khoa Tâm thần'),
    #     ('15', 'Khoa Thần kinh')
    # )
    patient = models.ForeignKey(PatientModel, on_delete=models.CASCADE)
    encounter_identifier = models.CharField(max_length=100, primary_key=True)
    encounter_start = models.DateTimeField(default=datetime.now)
    encounter_end = models.DateTimeField(null=True)
    encounter_length = models.CharField(max_length=100, null=True)
    encounter_status = models.CharField(max_length=20, default='queued')
    encounter_class = models.CharField(
        default="AMB", null=True, max_length=10, choices=CLASS_CHOICES)
    encounter_type = models.CharField(
        default="2", null=True, max_length=30, choices=TYPE_CHOICES)
    encounter_service = models.CharField(null=True, max_length=20)
    encounter_priority = models.CharField(
        null=True, max_length=10, choices=PRIORITY_CHOICES)
    encounter_reason = models.CharField(null=True, max_length=10)
    # encounter_location = models.CharField(null=True,max_length=20, choices=LOCATION_CHOICES)
    encounter_participant = models.CharField(max_length=100, null=True)
    encounter_version = models.IntegerField(default=0)
    encounter_storage = models.CharField(max_length=100, default='local')

class ConditionModel(models.Model):
    CLINICAL_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('recurrence', 'Recurrence'),
        ('relapse', 'Relapse'),
        ('remission', 'Remission'),
        ('resolved', 'Resolves')
    )
    SEVERITY_CHOICES = (
        ('24484000', 'Nặng'),
        ('6736007', 'Vừa'),
        ('255604002', 'Nhẹ')
    )
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE)
    condition_identifier = models.CharField(max_length=100, primary_key=True)
    condition_code = models.CharField(max_length=100, default='')
    condition_clinical_status = models.CharField(
        max_length=100, choices=CLINICAL_CHOICES, blank=True)
    condition_verification_status = models.CharField(max_length=100, default='confirmed')
    condition_category = models.CharField(max_length=100, null=True)
    condition_onset = models.DateField(null=True, blank=True)
    condition_abatement = models.DateField(null=True, blank=True)
    condition_severity = models.CharField(
        choices=SEVERITY_CHOICES, max_length=100)
    condition_asserter = models.CharField(max_length=100, null=True)
    condition_note = models.CharField(max_length=100, null=True, blank=True)
    condition_version = models.IntegerField(default=0)


class ServiceRequestModel(models.Model):
    SERVICE_STATUS_CHOICES = (
        ('draft', 'Nháp'),
        ('active', 'Đang hoạt động'),
        ('on-hold', 'Tạm giữ'),
        ('revoked', 'Đã thu hồi'),
        ('completed', 'Hoàn tất'),
        ('entered-in-error', 'Nhập sai'),
        ('unknown', 'Không xác định')
    )
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE)
    service_identifier = models.CharField(max_length=100, primary_key=True)
    service_status = models.CharField(default='active', max_length=100, choices=SERVICE_STATUS_CHOICES)
    service_intent = models.CharField(max_length=100, default='order')
    service_category = models.CharField(max_length=10)
    service_code = models.CharField(max_length=100, null=True)
    service_occurrence = models.DateField(max_length=100)
    service_authored = models.DateField(max_length=100)
    service_requester = models.CharField(max_length=100,null=True)
    service_note = models.CharField(max_length=100, null=True)
    service_performer = models.CharField(max_length=100, default='')
    service_version = models.IntegerField(default=0)


class ObservationModel(models.Model):
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE)
    service_identifier = models.ForeignKey(ServiceRequestModel, on_delete=models.CASCADE, null=True)
    observation_identifier = models.CharField(max_length=100, primary_key=True)
    observation_status = models.CharField(default='registered', max_length=10)
    observation_category = models.CharField(default='', max_length=10)
    observation_code = models.CharField(default='', max_length=100)
    observation_effective = models.DateTimeField(default=datetime.now)
    observation_performer = models.CharField(default='', max_length=100)
    observation_value_quantity = models.CharField(
        default='', max_length=10, null=True)
    observation_value_unit = models.CharField(default='', max_length=10)
    observation_note = models.CharField(default='', max_length=300, null=True)
    observation_reference_range = models.CharField(max_length=100, null=True)
    observation_version = models.IntegerField(default=0)


class ProcedureModel(models.Model):
    PROCEDURE_CATEGORY_CHOICES = (
        ('22642003', 'Phương pháp hoặc dịch vụ tâm thần'),
        ('409063005', 'Tư vấn'),
        ('409073007', 'Giáo dục'),
        ('387713003', 'Phẫu thuật'),
        ('103693007', 'Chuẩn đoán'),
        ('46947000', 'Phương pháp chỉnh hình'),
        ('410606002', 'Phương pháp dịch vụ xã hội')
    )
    PROCEDURE_OUTCOME_CHOICES = (
        ('385669000', 'Thành công'),
        ('385671000', 'Không thành công'),
        ('385670004', 'Thành công một phần')
    )
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE)
    service_identifier = models.OneToOneField(ServiceRequestModel, on_delete=models.CASCADE)
    procedure_identifier = models.CharField(max_length=100, primary_key=True)
    procedure_status = models.CharField(max_length=100)
    procedure_category = models.CharField(
        max_length=100, choices=PROCEDURE_CATEGORY_CHOICES)
    procedure_code = models.CharField(max_length=100)
    procedure_performed_datetime = models.DateTimeField(null=True)
    procedure_asserter = models.CharField(max_length=100, null=True)
    procedure_performer = models.CharField(max_length=100, null=True)
    procedure_location = models.CharField(max_length=100, null=True)
    procedure_reason_code = models.CharField(max_length=100, null = True)
    procedure_outcome = models.CharField(max_length=100, null=True, choices=PROCEDURE_OUTCOME_CHOICES)
    procedure_complication = models.CharField(max_length=100, null=True)
    procedure_follow_up = models.CharField(max_length=100, null=True)
    procedure_note = models.CharField(max_length=100, null=True)
    procedure_used = models.CharField(max_length=100, null=True)
    procedure_version = models.IntegerField(default=0)


class AllergyModel(models.Model):
    CATEGORY_CHOICES = (
        ('food', 'thức ăn'),
        ('medication', 'thuốc'),
        ('environment', 'môi trường'),
        ('biologic', 'sinh vật')
    )
    CLINICAL_CHOICES = (
        ('active', 'đang hoạt động'),
        ('inactive', 'không hoạt động'),
        ('resolved', 'đã khỏi')
    )
    CRITICALITY_CHOICES = (
        ('low', 'mức độ thấp'),
        ('high', 'mức độ cao'),
        ('unable-to-assess', 'không đánh giá được')
    )
    SEVERITY_CHOICES = (
        ('mild', 'nhẹ'),
        ('moderate', 'vừa phải'),
        ('severe', 'dữ dội')
    )
    encounter_identifier = models.ForeignKey(EncounterModel, on_delete=models.CASCADE)
    allergy_identifier = models.CharField(max_length=100,primary_key=True)
    allergy_clinical_status = models.CharField(max_length=100, choices=CLINICAL_CHOICES)
    allergy_verification_status = models.CharField(max_length=100, default='confirmed')
    allergy_type = models.CharField(max_length=100, default='allergy')
    allergy_category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    allergy_code = models.CharField(max_length=100)
    allergy_criticality = models.CharField(max_length=100, choices=CRITICALITY_CHOICES)
    allergy_onset = models.DateField(null=True)
    allergy_last_occurrence = models.DateField(null=True)
    allergy_reaction_substance = models.CharField(max_length=100, null=True, blank=True)
    allergy_reaction_manifestation = models.CharField(max_length=100, null=True)
    allergy_reaction_severity = models.CharField(max_length=100, choices=SEVERITY_CHOICES, blank=True)
    allergy_reaction_note = models.CharField(max_length=100, null=True, blank=True)
    allergy_version = models.IntegerField(default=0)


class MedicationModel(models.Model):
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
    UNIT_CHOICES = (
        ('s', 'giây'),
        ('min', 'phút'),
        ('h', 'giờ'),
        ('d', 'ngày'),
        ('wk', 'tuần'),
        ('mo', 'tháng'),
        ('a', 'năm')
    )
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE)
    medication_identifier = models.CharField(max_length=100, primary_key=True)
    medication_status = models.CharField(max_length=100, default='active')
    medication_medication = models.CharField(max_length=100)
    medication_effective = models.DateField()
    medication_date_asserted = models.DateField(null=True)
    medication_reason_code = models.CharField(max_length=100, default='')
    dosage_additional_instruction = models.CharField(max_length=100, blank=True)
    dosage_patient_instruction = models.CharField(max_length=100, blank=True)
    dosage_frequency = models.CharField(max_length=10)
    dosage_period = models.CharField(max_length=10)
    dosage_period_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, null=True)
    dosage_duration = models.CharField(max_length=10)
    dosage_duration_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, null=True)
    dosage_route = models.CharField(max_length=100)
    dosage_quantity = models.CharField(max_length=10)
    dosage_when = models.CharField(choices=DOSAGE_WHEN_CHOICES, max_length=100, blank=True)
    dosage_offset = models.CharField(max_length=10, null=True)
    medication_version = models.IntegerField(default=0)


class DiagnosticReportModel(models.Model):
    encounter_identifier = models.ForeignKey(
        EncounterModel, on_delete=models.CASCADE
    )
    service_identifier = models.OneToOneField(
        ServiceRequestModel, on_delete=models.CASCADE
    )
    diagnostic_identifier = models.CharField(max_length=100, primary_key=True)
    diagnostic_status = models.CharField(max_length=100)
    diagnostic_category = models.CharField(max_length=100)
    diagnostic_code = models.CharField(max_length=100)
    diagnostic_effective = models.DateTimeField(null = True)
    diagnostic_performer = models.CharField(max_length=100)
    diagnostic_conclusion = models.CharField(max_length=1000)
    diagnostic_version = models.IntegerField(default=0)


class DischargeDiseases(models.Model):
    disease_code = models.CharField(max_length=10)
    disease_name = models.CharField(max_length=100)    
    disease_search = models.CharField(max_length=100)


class ComorbidityDiseases(models.Model):
    discharge_diseases = models.ForeignKey(DischargeDiseases, on_delete=models.CASCADE)
    disease_code = models.CharField(max_length=10)
    disease_name = models.CharField(max_length=100)
    disease_search = models.CharField(max_length=100)
    


class ScheduleModel(models.Model):
    practitioner_name = models.CharField(max_length=100)
    practitioner_identifier = models.CharField(max_length=20)
    practitioner_location = models.CharField(max_length=100, null=True)
    schedule_date = models.DateField()
    session = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    
    