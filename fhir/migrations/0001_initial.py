# Generated by Django 3.2 on 2021-12-15 17:33

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('administration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DischargeDisease',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disease_code', models.CharField(max_length=10)),
                ('disease_name', models.CharField(max_length=100)),
                ('disease_search', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='EncounterModel',
            fields=[
                ('encounter_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('encounter_start', models.DateTimeField(default=datetime.datetime.now)),
                ('encounter_end', models.DateTimeField(null=True)),
                ('encounter_length', models.CharField(max_length=100, null=True)),
                ('encounter_status', models.CharField(default='queued', max_length=20)),
                ('encounter_class', models.CharField(choices=[('IMP', 'Nội trú'), ('AMB', 'Ngoại trú'), ('FLD', 'Khám tại địa điểm ngoài'), ('EMER', 'Khẩn cấp'), ('HH', 'Khám tại nhà'), ('ACUTE', 'Nội trú khẩn cấp'), ('NONAC', 'Nội trú không khẩn cấp'), ('OBSENC', 'Thăm khám quan sát'), ('SS', 'Thăm khám trong ngày'), ('VR', 'Trực tuyến'), ('PRENC', 'Tái khám')], default='AMB', max_length=10, null=True)),
                ('encounter_type', models.CharField(choices=[('Bệnh án nội khoa', 'Bệnh án nội khoa'), ('Bệnh án ngoại khoa', 'Bệnh án ngoại khoa'), ('Bệnh án phụ khoa', 'Bệnh án phụ khoa'), ('Bệnh án sản khoa', 'Bệnh án sản khoa')], default='2', max_length=30, null=True)),
                ('encounter_service', models.CharField(max_length=20, null=True)),
                ('encounter_priority', models.CharField(choices=[('A', 'ASAP'), ('EL', 'Tự chọn'), ('EM', 'Khẩn cấp'), ('P', 'Trước'), ('R', 'Bình thường'), ('S', 'Star')], max_length=10, null=True)),
                ('encounter_reason', models.CharField(max_length=10, null=True)),
                ('encounter_participant', models.CharField(max_length=100, null=True)),
                ('encounter_version', models.IntegerField(default=0)),
                ('encounter_storage', models.CharField(default='local', max_length=100)),
                ('encounter_location', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.clinicaldepartment')),
                ('encounter_participant_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.practitionermodel')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_name', models.CharField(max_length=1000)),
                ('image_category', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Medicine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicine_name', models.CharField(max_length=200, unique=True)),
                ('medicine_unit', models.CharField(max_length=50, null=True)),
                ('medicine_price_on_unit', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PatientModel',
            fields=[
                ('identifier', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=100)),
                ('birthdate', models.DateField(default=datetime.datetime.now)),
                ('gender', models.CharField(choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], default='', max_length=3)),
                ('work_address', models.CharField(default='', max_length=255)),
                ('home_address', models.CharField(default='', max_length=255)),
                ('telecom', models.CharField(default='', max_length=10)),
                ('group_name', models.CharField(default='patient', max_length=20)),
                ('contact_relationship', models.CharField(blank=True, choices=[('C', 'Liên hệ khẩn cấp'), ('E', 'Chủ sở hữu lao động'), ('F', 'Cơ quan liên bang'), ('I', 'Công ty bảo hiểm'), ('N', 'Người nối dõi'), ('S', 'Cơ quan nhà nước'), ('U', 'Không xác định')], default='C', max_length=100, null=True)),
                ('contact_name', models.CharField(blank=True, max_length=100, null=True)),
                ('contact_telecom', models.CharField(blank=True, max_length=100, null=True)),
                ('contact_address', models.CharField(blank=True, max_length=100, null=True)),
                ('contact_gender', models.CharField(blank=True, choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=1000)),
                ('test_category', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceRequestModel',
            fields=[
                ('service_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('service_status', models.CharField(choices=[('draft', 'Nháp'), ('active', 'Đang hoạt động'), ('on-hold', 'Tạm giữ'), ('revoked', 'Đã thu hồi'), ('completed', 'Hoàn tất'), ('entered-in-error', 'Nhập sai'), ('unknown', 'Không xác định')], default='draft', max_length=100)),
                ('service_intent', models.CharField(default='order', max_length=100)),
                ('service_category', models.CharField(max_length=100)),
                ('service_code', models.CharField(max_length=100, null=True)),
                ('service_occurrence', models.DateField(max_length=100)),
                ('service_authored', models.DateTimeField(max_length=100)),
                ('service_performed_date', models.DateField(max_length=100, null=True)),
                ('service_requester', models.CharField(max_length=100, null=True)),
                ('service_note', models.CharField(blank=True, max_length=100, null=True)),
                ('service_performer', models.CharField(max_length=100, null=True)),
                ('service_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
                ('serivce_requester_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fhir.patientmodel')),
                ('service_performer_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.practitionermodel')),
            ],
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('practitioner_name', models.CharField(max_length=100)),
                ('practitioner_location', models.CharField(max_length=100, null=True)),
                ('schedule_date', models.DateField()),
                ('session', models.CharField(max_length=20)),
                ('practitioner_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administration.practitionermodel')),
            ],
        ),
        migrations.CreateModel(
            name='ProcedureModel',
            fields=[
                ('procedure_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('procedure_status', models.CharField(max_length=100)),
                ('procedure_category', models.CharField(choices=[('22642003', 'Phương pháp hoặc dịch vụ tâm thần'), ('409063005', 'Tư vấn'), ('409073007', 'Giáo dục'), ('387713003', 'Phẫu thuật'), ('103693007', 'Chuẩn đoán'), ('46947000', 'Phương pháp chỉnh hình'), ('410606002', 'Phương pháp dịch vụ xã hội')], max_length=100)),
                ('procedure_code', models.CharField(max_length=100)),
                ('procedure_performed_datetime', models.DateTimeField(null=True)),
                ('procedure_performer', models.CharField(max_length=100, null=True)),
                ('procedure_location', models.CharField(max_length=100, null=True)),
                ('procedure_reason_code', models.CharField(max_length=100, null=True)),
                ('procedure_outcome', models.CharField(choices=[('385669000', 'Thành công'), ('385671000', 'Không thành công'), ('385670004', 'Thành công một phần')], max_length=100, null=True)),
                ('procedure_complication', models.CharField(blank=True, max_length=100, null=True)),
                ('procedure_follow_up', models.CharField(blank=True, max_length=100, null=True)),
                ('procedure_note', models.CharField(blank=True, max_length=100, null=True)),
                ('procedure_used', models.CharField(blank=True, max_length=100, null=True)),
                ('procedure_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
                ('procedure_performer_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.practitionermodel')),
                ('service_identifier', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fhir.servicerequestmodel')),
            ],
        ),
        migrations.CreateModel(
            name='ObservationModel',
            fields=[
                ('observation_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('observation_status', models.CharField(default='registered', max_length=10)),
                ('observation_category', models.CharField(default='', max_length=10)),
                ('observation_code', models.CharField(default='', max_length=100)),
                ('observation_effective', models.DateTimeField(default=datetime.datetime.now)),
                ('observation_performer', models.CharField(default='', max_length=100)),
                ('observation_value_quantity', models.CharField(default='', max_length=10, null=True)),
                ('observation_value_unit', models.CharField(default='', max_length=10)),
                ('observation_note', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('observation_reference_range', models.CharField(max_length=100, null=True)),
                ('observation_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
                ('service_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='fhir.servicerequestmodel')),
            ],
        ),
        migrations.CreateModel(
            name='MedicationModel',
            fields=[
                ('medication_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('medication_status', models.CharField(default='active', max_length=100)),
                ('medication_medication', models.CharField(max_length=100)),
                ('medication_effective', models.DateField()),
                ('medication_date_asserted', models.DateField(null=True)),
                ('medication_reason_code', models.CharField(default='', max_length=100)),
                ('dosage_additional_instruction', models.CharField(blank=True, max_length=100)),
                ('dosage_patient_instruction', models.CharField(blank=True, max_length=100)),
                ('dosage_frequency', models.PositiveIntegerField(default=1)),
                ('dosage_period', models.PositiveIntegerField(default=1)),
                ('dosage_period_unit', models.CharField(choices=[('s', 'giây'), ('min', 'phút'), ('h', 'giờ'), ('d', 'ngày'), ('wk', 'tuần'), ('mo', 'tháng'), ('a', 'năm')], max_length=10, null=True)),
                ('dosage_duration', models.PositiveIntegerField(default=1)),
                ('dosage_duration_unit', models.CharField(choices=[('s', 'giây'), ('min', 'phút'), ('h', 'giờ'), ('d', 'ngày'), ('wk', 'tuần'), ('mo', 'tháng'), ('a', 'năm')], max_length=10, null=True)),
                ('dosage_route', models.CharField(max_length=100)),
                ('dosage_quantity', models.PositiveIntegerField(default=1)),
                ('dosage_quantity_unit', models.CharField(max_length=10)),
                ('dosage_when', models.CharField(blank=True, choices=[('HS', 'dùng trước khi đi ngủ'), ('WAKE', 'dùng sau khi thức dậy'), ('C', 'dùng trong bữa ăn'), ('CM', 'dùng trong bữa sáng'), ('CD', 'dùng trong bữa trưa'), ('CV', 'dùng trong bữa tối'), ('AC', 'dùng trước bữa ăn'), ('ACM', 'dùng trước bữa sáng'), ('ACD', 'dùng trước bữa trưa'), ('ACV', 'dùng trước bữa tối'), ('PC', 'dùng sau bữa ăn'), ('PCM', 'dùng sau bữa sáng'), ('PCD', 'dùng sau bữa trưa'), ('PCV', 'dùng sau bữa tối')], max_length=100)),
                ('dosage_offset', models.CharField(max_length=10, null=True)),
                ('medication_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
            ],
        ),
        migrations.AddField(
            model_name='encountermodel',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.patientmodel'),
        ),
        migrations.CreateModel(
            name='DiagnosticReportModel',
            fields=[
                ('diagnostic_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('diagnostic_status', models.CharField(max_length=100)),
                ('diagnostic_category', models.CharField(max_length=100)),
                ('diagnostic_code', models.CharField(max_length=100)),
                ('diagnostic_effective', models.DateTimeField(null=True)),
                ('diagnostic_performer', models.CharField(max_length=100)),
                ('diagnostic_conclusion', models.CharField(max_length=1000)),
                ('diagnostic_version', models.IntegerField(default=0)),
                ('diagnostic_performer_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='administration.practitionermodel')),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
                ('service_identifier', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fhir.servicerequestmodel')),
            ],
        ),
        migrations.CreateModel(
            name='ConditionModel',
            fields=[
                ('condition_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('condition_code', models.CharField(default='', max_length=200)),
                ('condition_clinical_status', models.CharField(blank=True, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('recurrence', 'Recurrence'), ('relapse', 'Relapse'), ('remission', 'Remission'), ('resolved', 'Resolves')], max_length=100)),
                ('condition_verification_status', models.CharField(default='confirmed', max_length=100)),
                ('condition_category', models.CharField(max_length=100, null=True)),
                ('condition_onset', models.DateField(blank=True, null=True)),
                ('condition_abatement', models.DateField(blank=True, null=True)),
                ('condition_severity', models.CharField(choices=[('24484000', 'Nặng'), ('6736007', 'Vừa'), ('255604002', 'Nhẹ')], max_length=100)),
                ('condition_asserter', models.CharField(max_length=100, null=True)),
                ('condition_asserter_identifier', models.CharField(max_length=100, null=True)),
                ('condition_note', models.CharField(blank=True, max_length=100, null=True)),
                ('condition_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
            ],
        ),
        migrations.CreateModel(
            name='ComorbidityDisease',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disease_code', models.CharField(max_length=10)),
                ('disease_name', models.CharField(max_length=100)),
                ('disease_search', models.CharField(max_length=100)),
                ('discharge_diseases', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.dischargedisease')),
            ],
        ),
        migrations.CreateModel(
            name='AssignedEncounter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('practitioner_name', models.CharField(max_length=100)),
                ('practitioner_location', models.CharField(max_length=100, null=True)),
                ('encounter_date', models.DateField()),
                ('session', models.CharField(max_length=20)),
                ('assigned_encounter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
                ('practitioner_identifier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='administration.practitionermodel')),
            ],
        ),
        migrations.CreateModel(
            name='AllergyModel',
            fields=[
                ('allergy_identifier', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('allergy_clinical_status', models.CharField(choices=[('active', 'đang hoạt động'), ('inactive', 'không hoạt động'), ('resolved', 'đã khỏi')], max_length=100)),
                ('allergy_verification_status', models.CharField(default='confirmed', max_length=100)),
                ('allergy_type', models.CharField(default='allergy', max_length=100)),
                ('allergy_category', models.CharField(choices=[('food', 'thức ăn'), ('medication', 'thuốc'), ('environment', 'môi trường'), ('biologic', 'sinh vật')], max_length=100)),
                ('allergy_code', models.CharField(max_length=100)),
                ('allergy_criticality', models.CharField(choices=[('low', 'mức độ thấp'), ('high', 'mức độ cao'), ('unable-to-assess', 'không đánh giá được')], max_length=100)),
                ('allergy_onset', models.DateField(null=True)),
                ('allergy_last_occurrence', models.DateField(blank=True, null=True)),
                ('allergy_reaction_substance', models.CharField(blank=True, max_length=100, null=True)),
                ('allergy_reaction_manifestation', models.CharField(max_length=100, null=True)),
                ('allergy_reaction_severity', models.CharField(blank=True, choices=[('mild', 'nhẹ'), ('moderate', 'vừa phải'), ('severe', 'dữ dội')], max_length=100)),
                ('allergy_reaction_note', models.CharField(blank=True, max_length=100, null=True)),
                ('allergy_version', models.IntegerField(default=0)),
                ('encounter_identifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fhir.encountermodel')),
            ],
        ),
    ]
