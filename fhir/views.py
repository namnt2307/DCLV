from django.db import connection
from django.db.models import query
from django.shortcuts import render, redirect
from django.http import HttpResponse, request, HttpResponseRedirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, login
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaulttags import register
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from login.forms import UserCreationForm
from handlers import handlers
from .forms import EncounterForm, ConditionForm, ProcedureForm, ProcedureDetailForm, MedicationForm, ServiceRequestForm, DiagnosticReportForm, AllergyForm, PatientForm
from .models import AssignedEncounter, EncounterModel, MedicationModel, ServiceRequestModel, PatientModel, ConditionModel, ObservationModel, ProcedureModel, DiagnosticReportModel, AllergyModel, DischargeDisease, ComorbidityDisease, Schedule, Medicine, Test, Image, ImageResult
import xml.etree.ElementTree as ET
import requests
import uuid
import os
from lib import dttype as dt
# from fhir.forms import EHRCreationForm
from administration.models import PractitionerModel, ClinicalDepartment, Announcement
from datetime import datetime, timedelta, date
import time
import urllib.request
# Create your views here.


fhir_server = os.getenv('FHIR_SERVER', "http://34.101.85.15:8080/fhir")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def make_range(num):
    return range(num)


DOSAGE_WHEN_CHOICES = {
    'HS': 'dùng trước khi đi ngủ',
    'WAKE': 'dùng sau khi thức dậy',
    'C': 'dùng trong bữa ăn',
    'CM': 'dùng trong bữa sáng',
    'CD': 'dùng trong bữa trưa',
    'CV': 'dùng trong bữa tối',
    'AC': 'dùng trước bữa ăn',
    'ACM': 'dùng trước bữa sáng',
    'ACD': 'dùng trước bữa trưa',
    'ACV': 'dùng trước bữa tối',
    'PC': 'dùng sau bữa ăn',
    'PCM': 'dùng sau bữa sáng',
    'PCD': 'dùng sau bữa trưa',
    'PCV': 'dùng sau bữa tối'
}


GENDER_CHOICES = {
    'male': 'Nam',
    'female': 'Nữ'
}

PROCEDURE_OUTCOME_CHOICES = {
    'thành công': '385669000',
    'không thành công': '385671000',
    'thành công một phần': '385670004'
}

ENCOUNTER_CLASS_CHOICES = {
    'IMP': 'Nội trú',
    'AMB': 'Ngoại trú',
    'FLD': 'Khám tại địa điểm ngoài',
    'EMER': 'Khẩn cấp',
    'HH': 'Khám tại nhà',
    'ACUTE': 'Nội trú khẩn cấp',
    'NONAC': 'Nội trú không khẩn cấp',
    'OBSENC': 'Thăm khám quan sát',
    'SS': 'Thăm khám trong ngày',
    'VR': 'Trực tuyến',
    'PRENC': 'Tái khám'
}
ENCOUNTER_TYPE_CHOICES = {
    '1': 'Bệnh án nội khoa',
    '2': 'Bệnh án ngoại khoa',
    '3': 'Bệnh án phụ khoa',
    '4': 'Bệnh án sản khoa'
}
ENCOUNTER_PRIORITY_CHOICES = {
    'A': 'ASAP',
    'EL': 'Tự chọn',
    'EM': 'Khẩn cấp',
    'P': 'Trước',
    'R': 'Bình thường',
    'S': 'Star'
}
CONDITION_CLINICAL_CHOICES = {
    'active': 'Active',
    'inactive': 'Inactive',
    'recurrence': 'Recurrence',
    'relapse': 'Relapse',
    'remission': 'Remission',
    'resolved': 'Resolves'
}
CONDITION_SEVERITY_CHOICES = {
    '24484000': 'Nặng',
    '6736007': 'Vừa',
    '255604002': 'Nhẹ'
}
CONDITION_SEVERITY_VALUES = {
    'Nhẹ': '255604002',
    'Vừa': '6736007',
    'Nặng': '24484000'
}
SERVICE_REQUEST_CATEGORY_CHOICES = {
    'Laboratory procedure': '108252007',
    'Imaging': '363679005',
    'Counselling': '409063005',
    'Education': '409073007',
    'Surgical procedure': '387713003'
}
SERVICE_REQUEST_STATUS_CHOICES = {
    'draft': 'Nháp',
    'active': 'Đang hoạt động',
    'on-hold': 'Tạm giữ',
    'revoked': 'Đã thu hồi',
    'completed': 'Hoàn tất',
    'entered-in-error': 'Nhập sai',
    'unknown': 'Không xác định'
}
PROCEDURE_CATEGORY_CHOICES = {
    '22642003': 'Phương pháp hoặc dịch vụ tâm thần',
    '409063005': 'Tư vấn',
    '409073007': 'Giáo dục',
    '387713003': 'Phẫu thuật',
    '103693007': 'Chuẩn đoán',
    '46947000': 'Phương pháp chỉnh hình',
    '410606002': 'Phương pháp dịch vụ xã hội'
}
PROCEDURE_OUTCOME_CHOICES = {
    '385669000': 'Thành công',
    '385671000': 'Không thành công',
    '385670004': 'Thành công một phần'
}
DOSAGE_UNIT_CHOICES = {
    's': 'giây',
    'min': 'phút',
    'h': 'giờ',
    'd': 'ngày',
    'wk': 'tuần',
    'mo': 'tháng',
    'a': 'năm'
}
ALLERGY_CRITICALITY_CHOICES = {
    'low': 'mức độ thấp',
    'high': 'mức độ cao',
    'unable-to-assess': 'không đánh giá được'
}
ALLERGY_SEVERITY_CHOICES = {
    'mild': 'nhẹ',
    'moderate': 'vừa phải',
    'severe': 'dữ dội'
}
ALLERGY_CATEGORY_CHOICES = {
    'food': 'thức ăn',
    'medication': 'thuốc',
    'environment': 'môi trường',
    'biologic': 'sinh vật'
}
ALLERGY_STATUS_CHOICES = {
    'active': 'đang hoạt động',
    'inactive': 'không hoạt động',
    'resolved': 'đã khỏi'
}
CONTACT_RELATIONSHIP_CHOICES = {
    'C': 'Liên hệ khẩn cấp',
    'E': 'Chủ sở hữu lao động',
    'F': 'Cơ quan liên bang',
    'I': 'Công ty bảo hiểm',
    'N': 'Người nối dõi',
    'S': 'Cơ quan nhà nước',
    'U': 'Không xác định'
}

service_dict = {
    'Full Blood Count': {
        'WBC': {'unit': '/L', 'ref_range': '4.0 - 11.0'},
        'RBC': {'unit': '/L', 'ref_range': '4.10 - 5.20'},
        'HAEMOGLOBIN': {'unit': 'g/dl', 'ref_range': '12.50 - 17.50'},
        'PCV': {'unit': '%', 'ref_range': '40 -52'},
        'MCV': {'unit': 'fl', 'ref_range': '78 - 97'},
        'MCH': {'unit': 'pg', 'ref_range': '27 - 33'},
        'MCHC': {'unit': 'g/dl', 'ref_range': '31 - 36'},
        'PLATELET COUNT': {'unit': '/L', 'ref_range': '150 - 400'},
        'NEUTROPHIL': {'unit': '%', 'ref_range': '40 - 75'},
        'LYMPHOCYTE': {'unit': '%', 'ref_range': '20 - 45'},
        'MONOCYTE': {'unit': '%', 'ref_range': '2 - 10'},
        'EOSINOPHIL': {'unit': '%', 'ref_range': '1 - 6'},
        'BASOPHIL': {'unit': '%', 'ref_range': '0 - 1'},
        'RDW-SD': {'unit': 'fl', 'ref_range': '37.1 - 45.7'},
        'RDW-CV': {'unit': '%', 'ref_range': '12.0 - 13.6'},
        'PWD': {'unit': 'fl', 'ref_range': '10.1 - 16.1'},
        'MPV': {'unit': 'fl', 'ref_range': '9.3 - 12.1'},
        'P-LCR': {'unit': '%', 'ref_range': '18.5 - 42.3'},
        'PCT': {'unit': '%', 'ref_range': '0.17 - 0.32'}
    },
    'Full Blood Picture': {

    },
    'PT': {
        'PTT': {'unit': 's'},
        'INR': {'unit': ''}
    },
    'APTT': {
        'aPTT': {'unit': 's'}
    },
    'ESR': {},
    'G6PD Screening': {},
    'G6PD Assay': {},
    'Osmotic Fragility Test (OFT)': {},
    'Haemoglobinopathy Analysis': {},
    'Haemoglobin Electrophoresis': {},
    'NAP Score': {},
    'Bone Marrow Staining': {},
    'Thalassemia Screening': {},
    'Thalassemia Confirmation': {}
}

id_system = "urn:trinhcongminh"

ns = {'d': "http://hl7.org/fhir"}


def createobservations(encounter_instance, service_identifier, service_name):
    request_observations = service_dict.get(service_name, None)
    service_instance = ServiceRequestModel.objects.get(
        service_identifier=service_identifier)
    if request_observations:
        for key, value in request_observations.items():
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_instance, observation_identifier=service_identifier +
                                            '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f"), observation_status='final', observation_code=key, observation_category='laboratory', observation_value_unit=value['unit'], observation_reference_range=value['ref_range'])
    else:
        print('no valid data')


@login_required(login_url='/login/')
def user_app(request):
    announcements = Announcement.objects.all()    
    context = {
        'announcements': announcements
    }
    page = 'fhir/doctor.html'
    return render(request, page, context)


@login_required(login_url='/login/')
def manage(request):
    return render(request, 'fhir/manage.html')
# @login_required(login_url='/login/')
# def patient_view(request, group_name, user_name):
#     User = get_user_model()
#     patient = {}
#     user = User.objects.get(username=user_name)
#     user_id = user.identifier
#     if user:
#         patient['name'] = user.name
#         patient['gender'] = user.gender
#         patient['birthdate'] = user.birthdate
#         patient['address'] = [{'address': user.home_address, 'use': 'home'},
#                               {'address': user.work_address, 'use': 'work'}]
#         patient['identifier'] = user.identifier
#         message = 'Đây là hồ sơ của bạn'
#     else:
#         message = 'Bạn chưa có hồ sơ khám bệnh'
#     return render(request, 'fhir/patient/display.html', {'group_name': group_name, 'user_name': user_name, 'id': user_id, 'patient': patient, 'message': message})


class display_detail(LoginRequiredMixin, View):
    login_url = '/login/'
    # patient = get_user_model()

    def dispatch(self, request, *args, **kwargs):
        print(request.user.role)
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier):
        encounter_form = EncounterForm()
        patient_form = PatientForm()
        departments = {}
        department_categories = ClinicalDepartment.objects.filter(
            department_type='lâm sàng').order_by().values_list('department_category', flat=True).distinct()
        for category in department_categories:
            departments[category] = ClinicalDepartment.objects.filter(
                department_category=category)
        data = {'Patient': {}, 'Encounter': []}
        instance = PatientModel.objects.get(
            identifier=patient_identifier)
        data['Patient'] = instance
        try:
            encounters = EncounterModel.objects.filter(
                patient=patient_identifier, encounter_storage='hapi')
            for encounter in encounters:
                get_encounter = requests.get(fhir_server + "/Encounter?identifier=urn:trinhcongminh|" +
                                             encounter.encounter_identifier, headers={'Content-type': 'application/xml'})
                if 'entry' not in get_encounter.content.decode('utf-8'):
                    encounter.delete()
            get_encounter = requests.get(fhir_server + "/Encounter?subject.identifier=urn:trinhcongminh|" +
                                         patient_identifier, headers={'Content-type': 'application/xml'})
            if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_encounter.content.decode('utf-8'))
                data['Encounter'] = []
                for entry in get_root.findall('d:entry', ns):
                    encounter = {}
                    resource = entry.find('d:resource', ns)
                    encounter_resource = resource.find(
                        'd:Encounter', ns)
                    identifier = encounter_resource.find(
                        'd:identifier', ns)
                    encounter_identifier = identifier.find(
                        'd:value', ns).attrib['value']
                    encounter = dt.query_encounter(identifier.find(
                        'd:value', ns).attrib['value'], query_type='data')
                    print(encounter)
                    try:
                        encounter_instance = EncounterModel.objects.get(
                            encounter_identifier=encounter_identifier)
                        if encounter_instance.encounter_storage == 'hapi':
                            encounter_instance.delete()
                            EncounterModel.objects.create(
                                **encounter, patient=instance, encounter_storage='hapi')
                    except:
                        EncounterModel.objects.create(
                            **encounter, patient=instance, encounter_storage='hapi')
        except Exception as e:
            print(e)
            messages.error(request, "Kho FHIR không hoạt động")
        data['Encounter'] = EncounterModel.objects.all().filter(
            patient=patient_identifier)
        img_dir = f'/static/img/patient/{patient_identifier}.jpg'
        context = {
            'data': data,
            'img_dir': img_dir,
            'encounter_form': encounter_form,
            'patient_form': patient_form,
            'department_categories': department_categories,
            'departments': departments
        }
        print(context)
        return render(request, 'fhir/doctor/display.html', context)

    def post(self, request, patient_identifier):
        try:
            patient = PatientModel.objects.get(identifier=patient_identifier)
        except PatientModel.DoesNotExist:
            messages.errors(request, "Mã y tế cung cấp không tồn tại")
            return HttpResponseRedirect('/fhir/create')
        try:
            patient_id = dt.query_patient(patient_identifier, query_type='id')
            patient_update = PatientForm(
                request.POST or None, instance=patient)
            if patient_update.is_valid():
                patient_data = request.POST.copy()
                patient_data['id'] = patient_id['id']
                patient_resource = dt.create_patient_resource(patient_data)
                put_patient = requests.put(fhir_server + "/Patient/" + patient_id['id'], headers={
                                           'Content-type': 'application/xml'}, data=patient_resource.decode('utf-8'))
                if put_patient.status_code == 200:
                    patient_update.save()
                    messages.success(request, "Cập nhật thông tin thành công")
                    return HttpResponseRedirect(self.request.path_info)
                else:
                    messages.error(
                        request, "Cập nhật thông tin không thành công, hệ thống không cập nhật được trên FHIR")
                    return HttpResponseRedirect(self.request.path_info)
            else:
                print(patient_update.errors)
                messages.error(
                    request, "Cập nhật thông tin không thành công, thông tin cung cấp không phù hợp, vui lòng kiểm tra lại")
                return HttpResponseRedirect(self.request.path_info)
        except Exception as e:
            messages.error(
                request, "Kho FHIR không hoạt động, vui lòng thử lại sau")
            return HttpResponseRedirect(self.request.path_info)


class register(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = PatientForm()
        context = {
            'form': form
        }
        return render(request, 'fhir/doctor/create.html', context)

    def post(self, request):
        data = {'Patient': {}}
        try:
            connection_test = requests.get(fhir_server + "/Patient")
            if connection_test.status_code != 200:
                messages.error(
                    request, "Có lỗi khi kết nối với kho FHIR, vui lòng liên hệ kĩ thuật viên")
                return HttpResponseRedirect('/fhir/create/')
        except:
            messages.error(
                request, "Kho FHIR không hoạt động, vui lòng liên hệ kĩ thuật viên")
            return HttpResponseRedirect('/fhir/create/')
        try:
            PatientModel.objects.get(identifier=request.POST['identifier'])
            messages.error(
                request, "Mã y tế cung cấp đã tồn tại, vui lòng kiểm tra lại")
            return HttpResponseRedirect('/fhir/create/')
        except PatientModel.DoesNotExist:
            get_patient = requests.get(fhir_server + "/Patient?identifier=urn:trinhcongminh|" +
                                       request.POST['identifier'], headers={'Content-type': 'application/xml'})
            if get_patient.status_code == 200 and 'entry' in get_patient.content.decode('utf-8'):
                messages.error(
                    request, "Mã y tế cung cấp đã tồn tại, vui lòng kiểm tra lại")
                return HttpResponseRedirect('/fhir/create')
            else:
                patient_form = PatientForm(
                    request.POST or None)
                if patient_form.is_valid():
                    patient_form.save()
                    patient = dt.create_patient_resource(request.POST)
                    post_patient = requests.post(fhir_server + "/Patient/", headers={
                        'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                    user = get_user_model().objects.create_user(
                        username=request.POST['identifier'], password="1")
                    if post_patient.status_code == 201:
                        messages.success(request, "Tạo hồ sơ thành công")
                        return HttpResponseRedirect('/fhir/display_detail/' + request.POST['identifier'])
                    else:
                        messages.error(
                            request, "Thông tin cung cấp chính xác nhưng hệ thống có lỗi khi lưu hồ sơ lên FHIR, vui lòng liên hệ kĩ thuật viên")
                        return HttpResponseRedirect('/fhir/create/')
                else:
                    messages.error(
                        request, "Thông tin cung cấp không phù hợp, vui lòng kiểm tra lại")
                    return HttpResponseRedirect('/fhir/create/')


# class upload(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request, group_name, user_name):
#         return render(request, 'fhir/doctor/upload.html', {'group_name': group_name, 'user_name': user_name})

#     def post(self, request, group_name, user_name):
#         if request.FILES.get('excel_file'):
#             excel_file = request.FILES.get('excel_file')
#             data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
#             data = dt.get_patient_upload_data(excel_file)
#             patient = dt.create_patient_resource(data['Patient'])
#             put_req = None
#             post_patient = None
#             encounter_id = None
#             data['Patient']['id'] = dt.query_patient(
#                 data['Patient']['identifier'])['id']
#             if not data['Patient']['id']:
#                 # patient = dt.create_patient_resource(data['Patient'])
#                 # put_req = requests.put(fhir_server + "/Patient/"+data['Patient']['id'], headers={
#                 #                        'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
#             # else:
#                 post_patient = requests.post(fhir_server + "/Patient/", headers={
#                                          'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
#                 if post_patient.status_code == 201:

#             if post_req and post_req.status_code == 201:

#                 get_root = ET.fromstring(post_patient.content.decode('utf-8'))
#                 id_resource = get_root.find('d:id', ns)
#                 patient_id = id_resource.attrib['value']
#                 encounter = dt.create_encounter_resource(
#                     data['Encounter'], patient_id, data['Patient']['name'])
#                 post_req = requests.post(fhir_server + "/Encounter/", headers={
#                                          'Content-type': 'application/xml'}, data=encounter.decode('utf-8'))
#                 if post_req.status_code == 201:
#                     get_root = ET.fromstring(post_req.content.decode('utf-8'))
#                     id_resource = get_root.find('d:id', ns)
#                     encounter_id = id_resource.attrib['value']
#                     data['Encounter']['id'] = encounter_id
#                 if data['Observation']:
#                     for i in range(len(data['Observation'])):
#                         observation = dt.create_observation_resource(
#                             data['Observation'][i], data['Patient']['name'], patient_id, encounter_id)
#                         post_req = requests.post(fhir_server + "/Observation/", headers={
#                                                  'Content-type': 'application/xml'}, data=observation.decode('utf-8'))
#                         print(post_req.status_code)
#                         print(post_req.content)
#                 data['encounter_type'] = 'dict'
#                 if data['Encounter']['period']['start']:
#                     data['Encounter']['period']['start'] = dt.getdatetime(
#                         data['Encounter']['period']['start'])
#                 if data['Encounter']['period']['end']:
#                     data['Encounter']['period']['end'] = dt.getdatetime(
#                         data['Encounter']['period']['end'])
#                 return render(request, 'fhir/doctor/display.html', {'message': 'Upload successful', 'data': data, 'group_name': group_name, 'user_name': user_name})
#             else:
#                 return render(request, 'fhir/doctor.html', {'message': 'Failed to create resource, please check your file!', 'group_name': group_name, 'user_name': user_name})
#         else:
#             return render(request, 'fhir/doctor.html', {'message': 'Please upload your file!', 'group_name': group_name, 'user_name': user_name})


class upload(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        return render(request, 'fhir/doctor/upload.html')

    def post(self, request):
        if request.FILES.get('excel_file'):
            user = get_user_model()
            excel_file = request.FILES.get('excel_file')
            data = {}
            data = dt.get_patient_upload_data(excel_file)
            patient = dt.create_patient_resource(data['Patient'])
            post_patient = None
            encounter_id = None
            try:
                user.objects.get(identifier=patient['identifier'])
            except:
                user.objects.create_user(
                    **patient, username=patient['identifier'], email='123@gmail.com', password='123')
            data['Patient']['id'] = dt.query_patient(
                data['Patient']['identifier'])['id']
            if not data['Patient']['id']:
                post_patient = requests.post(fhir_server + "/Patient/", headers={
                    'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                if post_patient.status_code == 201:
                    root = ET.fromstring(post_patient.content.decode('utf-8'))
                    data['Patient']['id'] = root.find(
                        'd:id', ns).attrib['value']
            patient_id = data['Patient']['id']
            patient_instance = user.objects.get(
                identifier=patient['identifier'])
            encounter_instance = EncounterModel.create(
                **data['Encounter'], patient=patient_instance)

            post_encounter = None
            encounter = dt.create_encounter_resource(
                data['Encounter'], patient_id, data['Patient']['name'])
            post_encounter = requests.post(fhir_server + "/Encounter/", headers={
                'Content-type': 'application/xml'}, data=encounter.decode('utf-8'))
            if post_encounter.status_code == 201:
                root = ET.fromstring(post_encounter.content.decode('utf-8'))
                id_resource = root.find('d:id', ns)
                encounter_id = id_resource.attrib['value']
                data['Encounter']['id'] = encounter_id
                if data['Observation']:
                    for i in range(len(data['Observation'])):
                        observation_instance = ObservationModel.objects.create(
                            **data['Observation'][i], encounter_identifier=encounter_instance)
                        post_observation = None
                        observation = dt.create_observation_resource(
                            data['Observation'][i], patient_instance.name, patient_id, encounter_id)
                        post_observation = requests.post(fhir_server + "/Observation/", headers={
                            'Content-type': 'application/xml'}, data=observation.decode('utf-8'))
                if data['Condition']:
                    if data['Condition'].get('admission_by_patient'):
                        for condition in data['Condition']['admission_by_patient']:
                            condition_instance = ConditionModel.objects.create(
                                **condition, encounter_identifier=encounter_instance, condition_note='admission condition by patient')
                            pass
                    if data['Condition'].get('admission_by_doctor'):
                        for conditions in data['Condition']['admission_by_doctor']:
                            for key, value in conditions:
                                for condition in value:
                                    condition_instance = ConditionModel.objects.create(
                                        **condition, encounter_identifier=encounter_instance, condition_category=key, condition_note='admission condition by doctor')
                        pass
                    if data['Condition'].get('resolved_conditions'):
                        for condition in data['Condition']['resolved_conditions']:
                            condition_instance = ConditionModel.objects.create(
                                **condition, encounter_identifier=encounter_instance, condition_note='resolved condition by doctor')
                        pass
                    if data['Condition'].get('discharge_conditions'):
                        for condition in data['Condition']['discharge_conditions']:
                            condition_instance = ConditionModel.objects.create(
                                **condition, encounter_identifier=encounter_instance, condition_note='discharge condition by doctor')
                        pass
                    if data['Condition'].get('comorbidity_conditions'):
                        for condition in data['Condition']['comorbidity_conditions']:
                            condition_instance = ConditionModel.objects.create(
                                **condition, encounter_identifier=encounter_instance, condition_note='comorbidity condition by doctor')
                        pass
                if data['ServiceRequest']:
                    for service in data['ServiceRequest']:
                        service_instance = ServiceRequestModel.objects.create(
                            **service['service'], encounter_identifier=encounter_instance)
                        diagnostic_report_instance = DiagnosticReportModel.objects.create(
                            **service['diagnostic_report'], encounter_identifier=encounter_instance)
                    pass
            return render(request, 'fhir/doctor/display.html', {'message': 'Upload successful', 'data': data})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Failed to create resource, please check your file!'})
    # else:
        # return render(request, 'fhir/doctor.html', {'message': 'Please upload your file!', 'group_name': group_name, 'user_name': user_name})


class search(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        data = {'Patient': []}
        if request.GET.get('search_type'):
            if request.GET['search_type'] == 'identifier_type':
                try:
                    data['Patient'].append(PatientModel.objects.get(
                        identifier=request.GET['search_value']))
                except PatientModel.DoesNotExist:
                    try:
                        patient = dt.query_patient(
                            request.GET['search_value'], query_type='data')
                        if patient:
                            new_patient = PatientModel.objects.create(
                                **patient)
                            new_user = get_user_model().objects.create_user(
                                username=patient['identifier'], password="1")
                            data['Patient'].append(new_patient)
                        else:
                            messages.error(
                                request, "Không có dữ liệu với mã y tế đã nhập")
                            return HttpResponseRedirect(self.request.path_info)
                    except:
                        messages.error(
                            request, "Gặp lỗi khi kết nối với cơ sở dữ liệu FHIR")
                        return HttpResponseRedirect(self.request.path_info)
            elif request.GET['search_type'] == 'name_type':
                instance = PatientModel.objects.all().filter(
                    name=request.GET['search_value'])
                if len(instance) != 0:

                    data['Patient'] = instance
                else:
                    messages.error(
                        request, "Không có dữ liệu với tên đã nhập, sử dụng mã y tế để tìm kiếm")
                    return HttpResponseRedirect(self.request.path_info)
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database'})
        return render(request, 'fhir/doctor/search.html', {'data': data})

    def post(self, request):
        data = {'Patient': []}
        patient = get_user_model()
        if request.POST['search_type'] == 'identifier_type':
            try:
                data['Patient'].append(patient.objects.get(
                    identifier=request.POST['search_value']))
            except patient.DoesNotExist:
                data['Patient'] = dt.query_patient(
                    request.POST['search_value'], query_type='data')
                if data['Patient']:
                    new_patient = patient.objects.create_user(
                        **data['Patient'], username=data['Patient']['identifier'], email='123@gmail.com', password='123')
                    data['Patient'].append(new_patient)
        elif request.POST['search_type'] == 'name_type':
            instance = patient.objects.alL().filter(
                name=request.POST['search_value'])
            if instance != None:
                data['Patient'] = instance
                return HttpResponseRedirect(self.request.path_info)
            else:
                messages.error(
                    request, "Không có dữ liệu với tên đã nhập, sử dụng mã y tế để tìm kiếm")

            # for encounter in data['Encounter']:
            #     encounter['encounter_class'] = CLASS_CHOICES[encounter['encounter_class']]
            #     encounter['encounter_type'] = TYPE_CHOICES[encounter['encounter_type']]
            # return HttpResponseRedirect(f'/user/{group_name}/{user_name}/search/{patient_identifier}')
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database'})
        messages.success(request, "Welcome")
        return render(request, 'fhir/doctor/search.html', {'data': data})


class hanhchinh(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')

        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            print('abc')
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            print('encounter không tồn tại')
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):

        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = PatientModel.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, patient=patient['identifier'])
        data['Patient'] = instance
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        if encounter_instance.encounter_storage == 'hapi':
            pass
        elif encounter_instance.encounter_storage == 'local':
            pass
        if data:
            return render(request, 'fhir/hanhchinh.html', {'data': data})
        else:
            messages.error(request, "Không tìm thấy dữ liệu")
            return render(request, 'fhir/doctor.html')
        # else:
            # return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "medical assistant" and request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
            return super().dispatch(request, *args, **kwargs)
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')

    def post(self, request, patient_identifier):
        data = {'Patient': {}, 'Encounter': {}}
        print(request.POST)
        instance = PatientModel.objects.get(
            identifier=patient_identifier)
        encounters = EncounterModel.objects.filter(
            patient=patient_identifier).exclude(encounter_status="finished")
        print(encounters)
        if len(encounters) > 0:
            messages.error(request, "Bệnh nhân đang trong lần thăm khám khác")
            return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
        new_encounter_identifier = patient_identifier + \
            '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
        form = EncounterForm(request.POST)
        data['Patient'] = instance
        if form.is_valid():
            encounter = form.save(commit=False)
            encounter.encounter_identifier = new_encounter_identifier
            encounter.encounter_storage = 'local'
            encounter.patient = instance
            form.save()
        else:
            print(form.errors)
            messages.error(request, 'Thông tin cung cấp không hợp lệ')
            return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
        new_encounter = EncounterModel.objects.get(
            encounter_identifier=new_encounter_identifier)
        data['Encounter'] = new_encounter
        return redirect('/fhir/manage_schedule/')
        # return render(request, 'fhir/hanhchinh.html', {'group_name': group_name, 'user_name': user_name, 'data': data})


class dangky(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}}
        encounter_form = EncounterForm()
        data['Encounter'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Patient']['identifier'] = patient_identifier
        return render(request, 'fhir/dangky.html', {'data': data, 'form': encounter_form})

    def post(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}}
        data['Patient']['identifier'] = patient_identifier
        instance = PatientModel.objects.get(
            identifier=patient_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = EncounterForm(request.POST, instance=encounter_instance)
        if form.is_valid():
            new_encounter = form.save(commit=False)
            # encounter_n.encounter_identifier = encounter_identifier
            # encounter_n.patient = instance
            new_encounter.encounter_submitted = True
            form.save()
        data['Encounter'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        return render(request, 'fhir/dangky.html', {'data': data})


class hoibenh(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        admission_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by patient')
        resolved_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_identifier, condition_note='resolved condition by patient')
        allergies = AllergyModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        family_histories = None
        condition_form = ConditionForm()
        allergy_form = AllergyForm()
        context = {
            'data': data,
            'admission_conditions': admission_conditions,
            'resolved_conditions': resolved_conditions,
            'allergies': allergies,
            'family_histories': family_histories,
            'condition_form': condition_form,
            'allergy_form': allergy_form
        }
        return render(request, 'fhir/hoibenh.html', context)

    def post(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        patient = PatientModel.objects.get(identifier=patient_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        condition_identifier = encounter_identifier + '_' + \
            datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
        allergy_identifier = encounter_identifier + '_' + \
            datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
        if request.POST['classifier'] == 'benhly' or request.POST['classifier'] == 'tiensubanthan':
            if request.POST.get('condition_identifier'):
                condition_instance = ConditionModel.objects.get(
                    encounter_identifier=encounter_instance, condition_identifier=request.POST['condition_identifier'])
                condition_instance.condition_code = request.POST['condition_code']
                condition_instance.condition_onset = request.POST['condition_onset']
                if request.POST.get('condition_abatement'):
                    condition_instance.condition_abatement = request.POST['condition_abatement']
                    condition_instance.condition_clinical_status = 'inactive'
                else:
                    condition_instance.condition_clinical_status = 'active'
                condition_instance.condition_severity = request.POST['condition_severity']
                if request.POST['classifier'] == 'benhly':
                    condition_instance.condition_note = 'admission condition by patient'
                elif request.POST['classifier'] == 'tiensubanthan':
                    condition_instance.condition_note = 'resolved condition by patient'
                condition_instance.condition_asserter = patient.name
                condition_instance.condition_asserter_identifier = patient_identifier
                condition_instance.save()
            else:
                condition_object = {}
                condition_object['condition_identifier'] = condition_identifier
                condition_object['condition_code'] = request.POST['condition_code']
                condition_object['condition_onset'] = request.POST['condition_onset']
                if request.POST.get('condition_abatement'):
                    condition_object['condition_abatement'] = request.POST['condition_abatement']
                    condition_object['condition_clinical_status'] = 'inactive'
                else:
                    condition_object['condition_clinical_status'] = 'active'
                condition_object['condition_severity'] = request.POST['condition_severity']
                if request.POST['classifier'] == 'benhly':
                    condition_object['condition_note'] = 'admission condition by patient'
                elif request.POST['classifier'] == 'tiensubanthan':
                    condition_object['condition_note'] = 'resolved condition by patient'
                condition_object['condition_asserter'] = patient.name
                condition_object['condition_asserter_identifier'] = patient_identifier
                ConditionModel.objects.create(
                    encounter_identifier=encounter_instance, **condition_object)
        elif request.POST['classifier'] == 'diung':
            if request.POST.get('allergy_identifier'):
                allergy_instance = AllergyModel.objects.get(
                    allergy_identifier=request.POST['allergy_identifier'])
                form = AllergyForm(request.POST or None,
                                   instance=allergy_instance)
                if form.is_valid():
                    allergy = form.save(commit=False)
                    allergy.encounter_identifier = encounter_instance
                    form.save()
            else:
                form = AllergyForm(request.POST or None)
                if form.is_valid():
                    allergy = form.save(commit=False)
                    allergy.allergy_identifier = allergy_identifier
                    allergy.encounter_identifier = encounter_instance
                    form.save()
        elif request.POST['classifier'] == 'tiensugiadinh':
            pass
        return HttpResponseRedirect(self.request.path_info)


class khambenh(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        observation_instances = ObservationModel.objects.filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')
        observation_objects = {}
        condition_form = ConditionForm()
        for instance in observation_instances:
            if instance.observation_code.lower() == 'mạch':
                observation_objects['mach'] = instance
            elif instance.observation_code.lower() == 'nhịp thở':
                observation_objects['nhiptho'] = instance
            elif instance.observation_code.lower() == 'huyết áp tâm thu':
                observation_objects['tamthu'] = instance
            elif instance.observation_code.lower() == 'huyết áp tâm trương':
                observation_objects['tamtruong'] = instance
            elif instance.observation_code.lower() == 'cân nặng':
                observation_objects['cannang'] = instance
            elif instance.observation_code.lower() == 'nhiệt độ':
                observation_objects['nhietdo'] = instance
        condition_objects = {'toanthan': [], 'tuanhoan': [], 'hohap': [
        ], 'tieuhoa': [], 'tts': [], 'thankinh': [], 'cxk': [], 'tmh': [], 'rhm': [], 'mat': [], 'noitiet': []}
        condition_objects['toanthan'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='toanthan')

        condition_objects['tuanhoan'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='tuanhoan')

        condition_objects['hohap'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='hohap')

        condition_objects['tieuhoa'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='tieuhoa')

        condition_objects['tts'] = ConditionModel.objects.filter(encounter_identifier=encounter_instance,
                                                                 condition_note='admission condition by doctor', condition_category='tts')

        condition_objects['thankinh'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='thankinh')

        condition_objects['cxk'] = ConditionModel.objects.filter(encounter_identifier=encounter_instance,
                                                                 condition_note='admission condition by doctor', condition_category='cxk')

        condition_objects['tmh'] = ConditionModel.objects.filter(encounter_identifier=encounter_instance,
                                                                 condition_note='admission condition by doctor', condition_category='tmh')

        condition_objects['rhm'] = ConditionModel.objects.filter(encounter_identifier=encounter_instance,
                                                                 condition_note='admission condition by doctor', condition_category='rhm')

        condition_objects['mat'] = ConditionModel.objects.filter(encounter_identifier=encounter_instance,
                                                                 condition_note='admission condition by doctor', condition_category='mat')

        condition_objects['noitiet'] = ConditionModel.objects.filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by doctor', condition_category='noitiet')
        context = {
            'data': data,
            'observations': observation_objects,
            'conditions': condition_objects,
            'condition_form': condition_form,
            'severity': CONDITION_SEVERITY_CHOICES
        }
        return render(request, 'fhir/toanthan.html', context)

    def post(self, request, patient_identifier, encounter_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        if request.POST['classifier'] == 'observation':
            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='mạch', observation_category='vital-signs')
                if request.POST['mach']:
                    observation_instance.observation_value_quantity = request.POST['mach']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['mach']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance 
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='mạch'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['mach']
                    observation['observation_value_unit']='lần/ph'                        
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner
                    ObservationModel.objects.create(**observation)

            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='nhiệt độ', observation_category='vital-signs')
                if request.POST['nhietdo']:
                    observation_instance.observation_value_quantity = request.POST['nhietdo']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['nhietdo']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='nhiệt độ'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['nhietdo']
                    observation['observation_value_unit']='Cel'
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner
                    ObservationModel.objects.create(**observation)

            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='huyết áp tâm thu', observation_category='vital-signs')
                if request.POST['huyetaptamthu']:
                    observation_instance.observation_value_quantity = request.POST['huyetaptamthu']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['huyetaptamthu']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='huyết áp tâm thu'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['huyetaptamthu']
                    observation['observation_value_unit']='mmHg'
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner                    
                    ObservationModel.objects.create(**observation)

            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='huyết áp tâm trương', observation_category='vital-signs')
                if request.POST['huyetaptamtruong']:
                    observation_instance.observation_value_quantity = request.POST[
                        'huyetaptamtruong']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['huyetaptamtruong']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='huyết áp tâm trương'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['huyetaptamtruong']
                    observation['observation_value_unit']='mmHg'
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner
                    ObservationModel.objects.create(**observation)

            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='nhịp thở', observation_category='vital-signs')
                if request.POST['nhiptho']:
                    observation_instance.observation_value_quantity = request.POST['nhiptho']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['nhiptho']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='nhịp thở'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['nhiptho']
                    observation['observation_value_unit']='lần/ph'
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner
                    ObservationModel.objects.create(**observation)

            try:
                observation_instance = ObservationModel.objects.get(
                    encounter_identifier=encounter_instance, observation_code='cân nặng', observation_category='vital-signs')
                if request.POST['cannang']:
                    observation_instance.observation_value_quantity = request.POST['cannang']
                    observation_instance.save()
                else:
                    observation_instance.delete()
            except:
                if request.POST['cannang']:
                    observation = {}
                    observation_identifier = encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    observation['encounter_identifier']=encounter_instance
                    observation['observation_identifier']=observation_identifier
                    observation['observation_status']='final'
                    observation['observation_code']='cân nặng'
                    observation['observation_category']='vital-signs'
                    observation['observation_value_quantity']=request.POST['cannang']
                    observation['observation_value_unit']='kg'
                    observation['observation_performer'] = practitioner.name
                    observation['observation_performer_identifier'] = practitioner
                    ObservationModel.objects.create(**observation)
        elif request.POST['classifier'] == 'condition':
            if request.POST.get('condition_identifier'):
                condition_instance = ConditionModel.objects.get(
                    encounter_identifier=encounter_instance, condition_identifier=request.POST['condition_identifier'])
                condition_instance.condition_code = request.POST['condition_code']
                condition_instance.condition_clinical_status = 'active'
                condition_instance.condition_severity = request.POST['condition_severity']
                condition_instance.condition_note = 'admission condition by doctor'
                condition_instance.condition_asserter = practitioner.name
                condition_instance.condition_asserter_identifier = practitioner.identifier
                condition_instance.save()
            else:
                condition_identifier = encounter_identifier + '_' + \
                    datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                condition_object = {}
                condition_object['condition_identifier'] = condition_identifier
                condition_object['condition_code'] = request.POST['condition_code']
                condition_object['condition_clinical_status'] = 'active'
                condition_object['condition_severity'] = request.POST['condition_severity']
                condition_object['condition_note'] = 'admission condition by doctor'
                condition_object['condition_asserter'] = practitioner.name
                condition_object['condition_asserter_identifier'] = practitioner.identifier
                condition_object['condition_category'] = request.POST['condition_category']
                ConditionModel.objects.create(
                    encounter_identifier=encounter_instance, **condition_object)
        return HttpResponseRedirect(self.request.path_info)


class xetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

        # Checks pass, let http method handlers process the request

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance, service_category='Laboratory procedure')
        service_form = ServiceRequestForm()
        tests = {}
        test_categories = Test.objects.order_by().values_list(
            'test_category', flat=True).distinct()
        print(test_categories)
        for category in test_categories:
            tests[category] = Test.objects.filter(test_category=category)
        context = {
            'data': data,
            'services': services,
            'form': service_form,
            'test_categories': test_categories,
            'tests': tests
        }
        return render(request, 'fhir/xetnghiem.html', context)

    def post(self, request, patient_identifier, encounter_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = encounter_instance.encounter_identifier + \
                '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
            service.service_authored = timezone.localtime(timezone.now()).date()
            service.service_category = 'Laboratory procedure'
            service.service_requester = practitioner.name
            service.service_requester_identifier = practitioner
            form.save()
            createobservations(
                encounter_instance, service.service_identifier, service.service_code)
        # services = ServiceRequestModel.objects.all().filter(
        #     encounter_identifier=encounter_instance, service_category='laboratory')
        # service_form = ServiceRequestForm()
        # return render(request, 'fhir/xetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': service_form})
        return HttpResponseRedirect(self.request.path_info)


class chitietxetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical laboratory technician":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier') or not kwargs.get('service_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])
            if request.user.role == "doctor":
                if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                    # Redirect the user to somewhere else - add your URL here
                    messages.error(
                        request, "Bạn không có quyền truy cập trang này")
                    return HttpResponseRedirect('/')
            if kwargs['encounter_identifier'] not in kwargs['service_identifier']:
                messages.error(request, "Mã xét nghiệm không tồn tại")
                return HttpResponseRedirect("/fhir/" + kwargs['patient_identifier'] + "/" + kwargs['encounter_identifier'] + "/xetnghiem")
            try:
                service = ServiceRequestModel.objects.get(
                    service_identifier=kwargs['service_identifier'], service_category="Laboratory procedure")
                return super().dispatch(request, *args, **kwargs)
            except ServiceRequestModel.DoesNotExist:
                messages.error(request, "Mã xét nghiệm không tồn tại")
                return HttpResponseRedirect("/")
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

    def get(self, request, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        observation_instances = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        try:
            diagnostic_report_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_instance)
        except:
            diagnostic_report_instance = None
        diagnostic_form = DiagnosticReportForm()
        context = {
            'data': data,
            'service': service_instance,
            'observations': observation_instances,
            'diagnostic_report': diagnostic_report_instance,
            'diagnostic_form': diagnostic_form
        }
        return render(request, 'fhir/chitietxetnghiem.html', context)

    def post(self, request, patient_identifier, encounter_identifier, service_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        post = request.POST.copy()
        observation_dict = dict(request.POST)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        if observation_dict.get('diagnostic_report_conclusion'):
            diagnostic_report_conclusion = observation_dict['diagnostic_report_conclusion'][0]
            observation_dict.pop('diagnostic_report_conclusion')
            if observation_dict.get('diagnostic_report_identifier'):
                diagnostic_report_identifier = observation_dict['diagnostic_report_identifier'][0]
                observation_dict.pop('diagnostic_report_identifier')
                diagnostic_report = DiagnosticReportModel.objects.get(
                    diagnostic_identifier=diagnostic_report_identifier)
                diagnostic_report.diagnostic_effective = timezone.localtime(timezone.now())
                diagnostic_report.diagnostic_conclusion = diagnostic_report_conclusion
                diagnostic_report.save()
            else:
                diagnostic_report = {}
                diagnostic_report['diagnostic_identifier'] = encounter_identifier + '_' + \
                    datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                diagnostic_report['encounter_identifier'] = encounter_instance
                diagnostic_report['service_identifier'] = service_instance
                diagnostic_report['diagnostic_effective'] = timezone.localtime(timezone.now())
                diagnostic_report['diagnostic_status'] = 'final'
                diagnostic_report['diagnostic_category'] = service_instance.service_category
                diagnostic_report['diagnostic_code'] = service_instance.service_code
                diagnostic_report['diagnostic_performer'] = practitioner.name
                diagnostic_report['diagnostic_performer_identifier'] = practitioner
                diagnostic_report['diagnostic_conclusion'] = diagnostic_report_conclusion
                DiagnosticReportModel.objects.create(**diagnostic_report)
        for key, value in dict(list(observation_dict.items())[1:]).items():
            try:
                observation = ObservationModel.objects.get(
                    observation_identifier=key)
                observation.observation_code = value[0]
                observation.observation_value_quantity = value[1]
                observation.observation_reference_range = value[2]
                observation.observation_value_unit = value[3]
                observation.observation_performer = practitioner.identifier
                observation.observation_status = 'final'
                observation.save()
            except:
                print(value[0])
                print(value[1])
                if value[0] != '' and value[1] != '':
                    ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_instance, observation_identifier=service_identifier +
                                                    '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f"), observation_status='final', observation_code=value[0], observation_category='laboratory', observation_value_quantity=value[1], observation_value_unit=value[3], observation_reference_range=value[2])
        service_instance.service_performer = practitioner.name
        service_instance.service_performer_identifier = practitioner
        service_instance.save()
        return HttpResponseRedirect(self.request.path_info)


class thuthuat(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        service_form = ServiceRequestForm()
        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        return render(request, 'fhir/thuthuat.html', {'data': data, 'service_form': service_form, 'form': procedure_form, 'procedures': procedures, 'procedure_category': PROCEDURE_CATEGORY_CHOICES})

    def post(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        service_instances = ServiceRequestModel.objects.filter(
            encounter_identifier=encounter_instance)
        service_identifier = encounter_identifier + \
            '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
        form = ServiceRequestForm(request.POST)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = service_identifier
            service.service_authored = timezone.localtime(timezone.now()).date()
            service.service_category = 'laboratory'
            service.service_requester = practitioner.name
            service.service_requester_identifier = practitioner
            form.save()

        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        context = {
            'data': data,
            'form': procedure_form,
            'procedures': procedures,
            'procedure_category': PROCEDURE_CATEGORY_CHOICES
        }
        return render(request, 'fhir/thuthuat.html')


class chitietthuthuat(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, patient_identifier, encounter_identifier, procedure_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        form = ProcedureDetailForm()
        procedure = ProcedureModel.objects.get(
            procedure_identifier=procedure_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=procedure_identifier)
        try:
            diagnostic_report_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_instance)
        except:
            diagnostic_report_instance = None
        diagnostic_form = DiagnosticReportForm()
        context = {
            'data': data,
            'services': services,
            'procedure': procedure,
            'form': form,
            'diagnostic_report': diagnostic_report_instance,
            'diagnostic_form': diagnostic_form
        }
        return render(request, 'fhir/chitietthuthuat.html', context)

    def post(self, request, patient_identifier, encounter_identifier, procedure_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_instance = ProcedureModel.objects.get(
            procedure_identifier=procedure_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        form = ProcedureDetailForm(request.POST, instance=procedure_instance)
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.procedure_status = 'completed'
            procedure.procedure_performed_datetime = timezone.localtime(timezone.now())
            procedure.procedure_performer = practitioner.name
            procedure.procedure_performer_identifier = practitioner
            form.save()
        context = {
            'data': data,
            'services': services,
            'procedure': procedure_instance,
            'form': form
        }
        return HttpResponseRedirect(self.request.path_info)


class thuoc(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        medications = MedicationModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        medication_form = MedicationForm()
        condition_form = ConditionForm()
        condition_displays = {}
        discharge_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_instance, condition_note='discharge condition by doctor')
        for condition in discharge_conditions:
            condition_displays[condition.condition_identifier] = []
            if ' ' in condition.condition_code:
                codes = condition.condition_code.split(' ')
                for code in codes:
                    condition_displays[condition.condition_identifier].append(
                        DischargeDisease.objects.get(disease_code=code))
            else:
                condition_displays[condition.condition_identifier].append(
                    DischargeDisease.objects.get(disease_code=condition.condition_code))
        comorbidity_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_instance, condition_note='comorbidity condition by doctor')
        for condition in comorbidity_conditions:
            condition_displays[condition.condition_identifier] = []
            if ' ' in condition.condition_code:
                codes = condition.condition_code.split(' ')
                for code in codes:
                    condition_displays[condition.condition_identifier].append(
                        DischargeDisease.objects.get(disease_code=code))
            else:
                condition_displays[condition.condition_identifier].append(
                    DischargeDisease.objects.get(disease_code=condition.condition_code))
        discharge_diseases = DischargeDisease.objects.all()
        comorbidity_diseases = ComorbidityDisease.objects.all()
        medicines = Medicine.objects.all()
        medicine_unit = Medicine.objects.order_by().values_list(
            'medicine_unit', flat=True).distinct()
        for unit in medicine_unit:
            print(unit)
        context = {
            'data': data,
            'medications': medications,
            'discharge_conditions': discharge_conditions,
            'comorbidity_conditions': comorbidity_conditions,
            'medication_form': medication_form,
            'condition_form': condition_form,
            'discharge_diseases': discharge_diseases,
            'comorbidity_diseases': comorbidity_diseases,
            'condition_displays': condition_displays,
            'medicines': medicines
        }
        return render(request, 'fhir/thuoc.html', context)

    def post(self, request, patient_identifier, encounter_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        if request.POST['classifier'] == 'medication':
            if request.POST.get('medication_identifier'):
                instance = MedicationModel.objects.get(
                    medication_identifier=request.POST['medication_identifier'])
                form = MedicationForm(request.POST or None, instance=instance)
                if form.is_valid():
                    medication = form.save(commit=False)
                    medication.medication_date_asserted = timezone.localtime(timezone.now()).date()
                    form.save()
            else:
                form = MedicationForm(request.POST or None)
                if form.is_valid():
                    medication = form.save(commit=False)
                    medication.encounter_identifier = encounter_instance
                    medication.medication_identifier = encounter_instance.encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    medication.medication_date_asserted = timezone.localtime(timezone.now()).date()
                    medication.medication_effective = timezone.localtime(timezone.now()).date()
                    form.save()
                else:
                    print(form.errors)
        else:
            post = request.POST.copy()
            post['condition_code'] = request.POST['condition_code'].replace(
                ',', ' ')
            request.POST = post
            if request.POST.get('condition_identifier'):
                instance = ConditionModel.objects.get(
                    condition_identifier=request.POST['condition_identifier'])
                form = ConditionForm(request.POST or None, instance=instance)
                if form.is_valid():
                    condition = form.save(commit=False)
                    condition.condition_clinical_status = 'active'
                    if request.POST['classifier'] == 'discharge':
                        condition.condition_note = 'discharge condition by doctor'
                    else:
                        condition.condition_note = 'comorbidity condition by doctor'
                    condition.condition_asserter = practitioner.name
                    condition.condition_asserter_identifier = practitioner.identifier
                    form.save()
            else:
                form = ConditionForm(request.POST)
                if form.is_valid():
                    condition = form.save(commit=False)
                    condition.condition_clinical_status = 'active'
                    condition.condition_identifier = encounter_instance.encounter_identifier + \
                        '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    condition.encounter_identifier = encounter_instance
                    if request.POST['classifier'] == 'discharge':
                        condition.condition_note = 'discharge condition by doctor'
                    else:
                        condition.condition_note = 'comorbidity condition by doctor'
                    condition.condition_asserter = practitioner.name
                    condition.condition_asserter_identifier = practitioner.identifier
                    form.save()
                else:
                    print(form.errors)
        # return render(request, 'fhir/thuoc.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'medications': medications, 'form': medication_form, 'when': DOSAGE_WHEN_CHOICES})
        return HttpResponseRedirect(self.request.path_info)


class hinhanh(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])

            if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                # Redirect the user to somewhere else - add your URL here
                messages.error(
                    request, "Bạn không có quyền truy cập trang này")
                return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        service_instances = ServiceRequestModel.objects.filter(
            encounter_identifier=encounter_instance, service_category='Imaging')
        service_form = ServiceRequestForm()
        images = {}
        image_categories = Image.objects.order_by().values_list(
            'image_category', flat=True).distinct()
        print(image_categories)
        for category in image_categories:
            images[category] = Image.objects.filter(image_category=category)
        context = {
            'data': data,
            'service_form': service_form,
            'services': service_instances,
            'image_categories': image_categories,
            'images': images,
            'status': SERVICE_REQUEST_STATUS_CHOICES
        }
        return render(request, 'fhir/hinhanh.html', context)

    def post(self, request, patient_identifier, encounter_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        new_service_identifier = encounter_identifier + \
            '_' + datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = new_service_identifier
            service.service_authored = timezone.localtime(timezone.now()).date()
            service.service_category = 'Imaging'
            service.service_requester = practitioner.name
            service.service_requester_identifier = practitioner
            form.save()
            service_instance = ServiceRequestModel.objects.get(
                service_identifier=new_service_identifier)
            new_procedure = ProcedureModel()
            new_procedure.encounter_identifier = encounter_instance
            new_procedure.service_identifier = service_instance
            new_procedure.procedure_identifier = new_service_identifier
            new_procedure.procedure_status = 'preparation'
            new_procedure.procedure_category = '103693007'
            new_procedure.procedure_code = service.service_code
            new_procedure.procedure_reason_code = service.service_reason_code
            new_procedure.save()
            return HttpResponseRedirect(self.request.path_info)
        else:
            return HttpResponse('Form is not valid')


class chitiethinhanh(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "diagnostic imaging technician":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier') or not kwargs.get('service_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])
            if request.user.role == "doctor":
                if self.request.user.username != encounter.encounter_participant_identifier.identifier:
                    # Redirect the user to somewhere else - add your URL here
                    messages.error(
                        request, "Bạn không có quyền truy cập trang này")
                    return HttpResponseRedirect('/')
            if kwargs['encounter_identifier'] not in kwargs['service_identifier']:
                messages.error(request, "Mã xét nghiệm không tồn tại")
                return HttpResponseRedirect("/fhir/" + kwargs['patient_identifier'] + "/" + kwargs['encounter_identifier'] + "/xetnghiem")
            try:
                service = ServiceRequestModel.objects.get(
                    service_identifier=kwargs['service_identifier'], service_category="Imaging")
                return super().dispatch(request, *args, **kwargs)
            except ServiceRequestModel.DoesNotExist:
                messages.error(request, "Mã xét nghiệm không tồn tại")
                return HttpResponseRedirect("/")
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

    def get(self, request, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        procedure_form = ProcedureDetailForm()
        procedure = ProcedureModel.objects.get(
            encounter_identifier=encounter_instance, service_identifier=service_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        images = ImageResult.objects.filter(procedure_identifier=procedure)
        try:
            diagnostic_report_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_instance)
        except:
            diagnostic_report_instance = None
        diagnostic_form = DiagnosticReportForm()
        context = {
            'data': data,
            'procedure_form': procedure_form,
            'service': service_instance,
            'procedure': procedure,
            'diagnostic_report': diagnostic_report_instance,
            'diagnostic_form': diagnostic_form,
            'images': images
        }
        return render(request, 'fhir/chitietthuthuat.html', context)

    def post(self, request, patient_identifier, encounter_identifier, service_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        procedure_instance = ProcedureModel.objects.get(
            encounter_identifier=encounter_instance, service_identifier=service_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        print(request.POST)
        print(request.FILES)
        form = ProcedureDetailForm(request.POST, instance=procedure_instance)
        if form.is_valid():
            print(request.POST)
            procedure = form.save(commit=False)
            procedure.procedure_status = 'completed'
            procedure.procedure_performer = practitioner.name
            procedure.procedure_performer_identifier = practitioner
            procedure.procedure_performed_datetime = timezone.localtime(timezone.now())
            form.save()
            if request.POST.get('diagnostic_report_conclusion'):
                if request.POST.get('diagnostic_report_identifier'):
                    diagnostic_report = DiagnosticReportModel.objects.get(
                        diagnostic_identifier=request.POST['diagnostic_report_identifier'])
                    diagnostic_report.diagnostic_effective = timezone.localtime(timezone.now())
                    diagnostic_report.diagnostic_conclusion = request.POST[
                        'diagnostic_report_conclusion']
                    diagnostic_report.save()
                else:
                    diagnostic_report = {}
                    diagnostic_report['diagnostic_identifier'] = encounter_identifier + '_' + \
                        datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
                    diagnostic_report['encounter_identifier'] = encounter_instance
                    diagnostic_report['service_identifier'] = service_instance
                    diagnostic_report['diagnostic_effective'] = timezone.localtime(timezone.now())
                    diagnostic_report['diagnostic_status'] = 'final'
                    diagnostic_report['diagnostic_category'] = service_instance.service_category
                    diagnostic_report['diagnostic_code'] = service_instance.service_code
                    diagnostic_report['diagnostic_performer'] = practitioner.name
                    diagnostic_report['diagnostic_performer_identifier'] = practitioner
                    diagnostic_report['diagnostic_conclusion'] = request.POST['diagnostic_report_conclusion']
                    DiagnosticReportModel.objects.create(**diagnostic_report)
            procedure_instance = ProcedureModel.objects.get(
                encounter_identifier=encounter_instance, service_identifier=service_identifier)
            if len(request.FILES) != 0:
                uploaded_images = ImageResult.objects.filter(procedure_identifier=procedure_instance)
                for image in uploaded_images:
                    os.remove(image.image.path)
                uploaded_images.delete()
                upload_images = request.FILES.getlist('result_images')
                for image in upload_images:
                    new_image = ImageResult.objects.create(procedure_identifier=procedure_instance, image=image)
            service_instance.service_performer = practitioner.name
            service_instance.service_performer_identifier = practitioner
            service_instance.save()
            service_instance.service_status = "completed"
            return HttpResponseRedirect(self.request.path_info)


class chandoan(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch():
        pass

    def get(self, request, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter'] = encounter_instance
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)

        try:
            diagnostic_report_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_instance)
        except:
            diagnostic_report_instance = None
        diagnostic_form = DiagnosticReportForm()
        context = {
            'data': data,
            'service': service_instance,
            'diagnostic_report': diagnostic_report_instance,
            'diagnostic_form': diagnostic_form
        }
        return render(request, 'fhir/chandoan.html', context)

    def post(self, request, patient_identifier, encounter_identifier, service_identifier):
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        practitioner = PractitionerModel.objects.get(
            identifier=request.user.username)
        if request.POST.get('diagnostic_identifier'):
            diagnostic_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_identifier)
            diagnostic_instance.diagnostic_conclusion = request.POST['diagnostic_conclusion']
            diagnostic_instance.diagnostic_performer = practitioner.name
            diagnostic_instance.diagnostic_performer_identifier = practitioner
            diagnostic_instance.diagnostic_effective = timezone.localtime(timezone.now())
            diagnostic_instance.save()
        else:
            diagnostic_identifier = encounter_identifier + '_' + \
                datetime.strftime(timezone.localtime(timezone.now()), "%d%m%Y%H%M%S%f")
            form = DiagnosticReportForm(request.POST)
            if form.is_valid():
                diagnostic = form.save(commit=False)
                diagnostic.encounter_identifier = encounter_instance
                diagnostic.service_identifier = service_instance
                diagnostic.diagnostic_identifier = diagnostic_identifier
                diagnostic.diagnostic_effective = timezone.localtime(timezone.now())
                diagnostic.diagnostic_status = 'final'
                diagnostic.diagnostic_category = service_instance.service_category
                diagnostic.diagnostic_code = service_instance.service_code
                diagnostic.diagnostic_performer = practitioner.name
                diagnostic.diagnostic_performer_identifier = practitioner
                form.save()
        diagnostic_instance = DiagnosticReportModel.objects.get(
            service_identifier=service_identifier)
        return HttpResponseRedirect(self.request.path_info)


class save(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        if not kwargs.get('encounter_identifier') or not kwargs.get('patient_identifier'):
            return HttpResponseRedirect('/login/')
        try:
            patient = PatientModel.objects.get(
                identifier=kwargs['patient_identifier'])
        except PatientModel.DoesNotExist:
            messages.error(request, "Mã y tế không tồn tại")
            return HttpResponseRedirect('/')
        if kwargs['patient_identifier'] not in kwargs['encounter_identifier']:
            messages.error(request, "Mã thăm khám không tồn tại")
            return HttpResponseRedirect('/')
        try:
            encounter = EncounterModel.objects.get(
                encounter_identifier=kwargs['encounter_identifier'])
            # if self.request.user.username != encounter.encounter_participant_identifier.identifier:
            #     # Redirect the user to somewhere else - add your URL here
            #     messages.error(request, "Bạn không có quyền truy cập trang này")
            #     return HttpResponseRedirect('/')
        except EncounterModel.DoesNotExist:
            messages.error(request, 'Mã thăm khám không tồn tại')
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)
    login_url = '/login/'

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Condition': []}
        participant = PractitionerModel.objects.get(
            identifier=request.user.username)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instances = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        for service in service_instances:
            if service.service_status != 'completed':
                messages.error(
                    request, "Có xét nghiệm/chẩn đoán chưa hoàn tất")
                return HttpResponseRedirect('/fhir/encounter/' + patient_identifier + '/' + encounter_identifier + '/hanhchinh')
        if encounter_instance.encounter_status != 'finished':
            encounter_instance.encounter_status = 'finished'
            encounter_instance.encounter_end = timezone.localtime(timezone.now())
            delta = encounter_instance.encounter_end.date(
            ) - encounter_instance.encounter_start.date()
            if delta.days == 0:
                encounter_instance.encounter_length = '1'
            else:
                encounter_instance.encounter_length = str(delta.days)
            encounter_instance.save()
            print(encounter_instance)
        try:
            connection_test = requests.get(fhir_server + "/Patient")
            if connection_test.status_code != 200:
                messages.error(
                    request, "Không thể kết nối đến kho FHIR, vui lòng liên hệ kĩ thuật viên")
                return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
        except:
            messages.error(
                request, "Kho FHIR không hoạt động, không thể chia sẻ dữ liệu")
            return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
        patient = dt.query_patient(patient_identifier, query_type='all')
        get_encounter = dt.query_encounter(
            encounter_identifier, query_type='id')
        participant_id = dt.query_practitioner(
            encounter_instance.encounter_participant_identifier.identifier, query_type='id')
        data['Encounter']['identifier'] = encounter_identifier
        data['Encounter']['status'] = encounter_instance.encounter_status
        data['Encounter']['period'] = {}
        data['Encounter']['period']['start'] = encounter_instance.encounter_start.strftime(
            '%Y-%m-%dT%H:%M:%S+07:00')
        data['Encounter']['period']['end'] = encounter_instance.encounter_end.strftime(
            '%Y-%m-%dT%H:%M:%S+07:00')
        data['Encounter']['class'] = encounter_instance.encounter_class
        data['Encounter']['type'] = encounter_instance.encounter_type
        data['Encounter']['service_type'] = encounter_instance.encounter_service
        data['Encounter']['priority'] = {}
        data['Encounter']['priority']['code'] = encounter_instance.encounter_priority
        data['Encounter']['priority']['display'] = encounter_instance.get_encounter_priority_display()
        data['Encounter']['location'] = encounter_instance.encounter_location.department_name
        data['Encounter']['reason_code'] = encounter_instance.encounter_reason
        data['Encounter']['length'] = encounter_instance.encounter_length
        print(data['Encounter'])
        if get_encounter:
            data['Encounter']['id'] = get_encounter['id']
        encounter_data = dt.create_encounter_resource(
            data['Encounter'], patient['id'], patient['name'], participant_id['id'], participant.name)
        # print(encounter_data)
        test_encounter = requests.post(fhir_server + "/Encounter/$validate", headers={
            'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
        print(test_encounter.content.decode('utf-8'))
        if get_encounter:
            put_encounter = requests.put(fhir_server + "/Encounter/" + get_encounter['id'], headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
            if put_encounter.status_code == 200:
                encounter_resource = ET.fromstring(
                    put_encounter.content.decode('utf-8'))
                encounter = dt.get_encounter(
                    encounter_resource, query_type='all')
            else:
                print("có lỗi khi lưu encounter")
        else:
            post_encounter = requests.post(fhir_server + "/Encounter/", headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
            if post_encounter.status_code == 201:
                encounter_resource = ET.fromstring(
                    post_encounter.content.decode('utf-8'))
                encounter = dt.get_encounter(
                    encounter_resource, query_type='all')
            else:
                print("có lỗi khi lưu allergy")
        if encounter:
            encounter_instance.encounter_version = encounter['version']
            encounter_instance.encounter_sharing_status = True
            encounter_instance.save()
            print(encounter_instance)
            condition_instances = ConditionModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for condition_instance in condition_instances:
                put_condition = None
                post_condition = None
                condition = {}
                condition['identifier'] = condition_instance.condition_identifier
                condition['clinical_status'] = condition_instance.condition_clinical_status
                condition['verification_status'] = condition_instance.condition_verification_status
                condition['category'] = condition_instance.condition_category
                if condition_instance.condition_asserter_identifier:
                    condition['asserter'] = {}
                    if "P" in condition_instance.condition_asserter_identifier:
                        condition['asserter']['type'] = "Practitioner"
                        condition['asserter']['id'] = dt.query_practitioner(
                            condition_instance.condition_asserter_identifier, query_type='id')['id']
                        condition['asserter']['name'] = condition_instance.condition_asserter
                    else:
                        condition['asserter']['type'] = "Patient"
                        condition['asserter']['id'] = dt.query_patient(
                            condition_instance.condition_asserter_identifier, query_type='id')['id']
                        condition['asserter']['name'] = condition_instance.condition_asserter
                condition['severity'] = {}
                condition['severity']['code'] = condition_instance.condition_severity
                condition['severity']['display'] = condition_instance.get_condition_severity_display(
                )
                condition['code'] = condition_instance.condition_code
                if condition['code']:
                    condition['display_code'] = ""
                    if ' ' in condition['code']:
                        codes = condition['code'].split(' ')
                        for code in codes:
                            try:
                                disease = DischargeDisease.objects.get(
                                    disease_code=code)
                                condition['display_code'] = (
                                    condition['display_code'] + " " + disease.disease_name).strip()
                            except:
                                break
                    else:
                        try:
                            disease = DischargeDisease.objects.get(
                                disease_code=condition['code'])
                            condition['display_code'] = disease.disease_name
                        except:
                            pass
                if condition_instance.condition_onset:
                    condition['onset'] = condition_instance.condition_onset.strftime(
                        '%Y-%m-%d')
                if condition_instance.condition_abatement:
                    condition['abatement'] = condition_instance.condition_abatement.strftime(
                        '%Y-%m-%d')
                condition['note'] = condition_instance.condition_note
                get_condition = dt.query_condition(
                    condition['identifier'], query_type='id')
                if get_condition:
                    condition['id'] = get_condition['id']
                condition_data = dt.create_condition_resource(
                    condition, patient['id'], patient['name'], encounter['id'])
                test_condition = requests.post(fhir_server + "/Condition/$validate",
                                               headers={'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
                print(test_condition.content.decode('utf-8'))
                if get_condition:
                    put_condition = requests.put(fhir_server + "/Condition/"+get_condition['id'], headers={
                        'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))

                    if put_condition.status_code == 200:
                        condition_resource = ET.fromstring(
                            put_condition.content.decode('utf-8'))
                        condition_meta = dt.get_condition(
                            condition_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu condition")
                else:
                    post_condition = requests.post(fhir_server + "/Condition/", headers={
                        'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
                    # print(post_condition.status_code)
                    if post_condition.status_code == 201:
                        condition_resource = ET.fromstring(
                            post_condition.content.decode('utf-8'))
                        condition_meta = dt.get_condition(
                            condition_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu condition")
                condition_instance.condition_version = condition_meta['version']
                condition_instance.save()
            allergy_instances = AllergyModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for allergy_instance in allergy_instances:
                put_allergy = None
                post_allergy = None
                allergy = {}
                allergy['identifier'] = allergy_instance.allergy_identifier
                allergy['clinical_status'] = {}
                allergy['clinical_status']['code'] = allergy_instance.allergy_clinical_status
                allergy['clinical_status']['display'] = allergy_instance.get_allergy_clinical_status_display()
                allergy['verification_status'] = allergy_instance.allergy_verification_status
                allergy['category'] = allergy_instance.allergy_category
                allergy['criticality'] = allergy_instance.allergy_criticality
                allergy['code'] = allergy_instance.allergy_code
                if allergy_instance.allergy_onset:
                    allergy['onset'] = allergy_instance.allergy_onset.strftime(
                        '%Y-%m-%d')
                if allergy_instance.allergy_last_occurrence:
                    allergy['last_occurrence'] = allergy_instance.allergy_last_occurrence.strftime(
                        '%Y-%m-%d')
                allergy['reaction'] = {}
                allergy['reaction']['substance'] = allergy_instance.allergy_reaction_substance
                allergy['reaction']['manifestation'] = allergy_instance.allergy_reaction_manifestation
                allergy['reaction']['severity'] = allergy_instance.allergy_reaction_severity
                get_allergy = dt.query_allergy(
                    allergy['identifier'], query_type='id')
                if get_allergy:
                    allergy['id'] = get_allergy['id']
                allergy_data = dt.create_allergy_resource(
                    allergy, patient['id'], patient['name'], encounter['id'])
                test_allergy = requests.post(fhir_server + '/AllergyIntolerance/$validate',
                                             headers={'Content-type': 'application/xml'}, data=allergy_data.decode('utf-8'))
                print(test_allergy.content.decode('utf-8'))
                if get_allergy:
                    put_allergy = requests.put(fhir_server + '/AllergyIntolerance/' + allergy['id'],  headers={
                        'Content-type': 'application/xml'}, data=allergy_data.decode('utf-8'))
                    if put_allergy.status_code == 200:
                        allergy_resource = ET.fromstring(
                            put_allergy.content.decode('utf-8'))
                    else:
                        print("có lỗi khi lưu allergy")
                else:
                    post_allergy = requests.post(fhir_server + '/AllergyIntolerance',  headers={
                        'Content-type': 'application/xml'}, data=allergy_data.decode('utf-8'))
                    if post_allergy.status_code == 201:
                        allergy_resource = ET.fromstring(
                            post_allergy.content.decode('utf-8'))
                    else:
                        print("có lỗi khi lưu allergy")
                allergy_meta = dt.get_condition(
                    allergy_resource, query_type='meta')
                allergy_instance.allergy_version = allergy_meta['version']
                allergy_instance.save()
            for service_instance in service_instances:
                put_service = None
                post_service = None
                service_instance.service_status = 'completed'
                service_instance.save()
                service_requester_id = dt.query_practitioner(
                    service_instance.service_requester_identifier.identifier, query_type='id')
                service_performer_id = dt.query_practitioner(
                    service_instance.service_performer_identifier.identifier, query_type='id')
                service = {}
                service['identifier'] = service_instance.service_identifier
                service['status'] = service_instance.service_status
                service['category'] = service_instance.service_category
                service['intent'] = service_instance.service_intent
                service['requester'] = {}
                service['requester']['id'] = service_requester_id['id']
                service['requester']['name'] = service_instance.service_requester
                service['performer'] = {}
                service['performer']['id'] = service_performer_id['id']
                service['performer']['name'] = service_instance.service_performer
                service['reason_code'] = service_instance.service_reason_code
                service['code'] = service_instance.service_code
                service['occurrence'] = service_instance.service_occurrence.strftime(
                    '%Y-%m-%d')
                service['authored_on'] = service_instance.service_authored.strftime(
                    '%Y-%m-%d')
                get_service = dt.query_service(
                    service['identifier'], query_type='id')
                if get_service:
                    service['id'] = get_service['id']
                service_data = dt.create_service_resource(
                    service, patient['id'], patient['name'], encounter['id'])
                test_service = requests.post(fhir_server + '/ServiceRequest/$validate', headers={                    
                    'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                print(test_service.content.decode('utf-8'))
                if get_service:
                    put_service = requests.put(fhir_server + "/ServiceRequest/" + get_service['id'], headers={
                        'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                    if put_service.status_code == 200:
                        service_resource = ET.fromstring(
                            put_service.content.decode('utf-8'))
                        service_meta = dt.get_service(
                            service_resource, query_type='all')
                    else:
                        print("có lỗi khi lưu service")
                else:
                    post_service = requests.post(fhir_server + "/ServiceRequest/", headers={
                        'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                    if post_service.status_code == 201:
                        service_resource = ET.fromstring(
                            post_service.content.decode('utf-8'))
                        service_meta = dt.get_service(
                            service_resource, query_type='all')
                    else:
                        print("có lỗi khi lưu service")
                service_instance.service_version = service_meta['version']
                service_instance.save()
                if (put_service and put_service.status_code == 200) or (post_service and post_service.status_code == 201):
                    service_observations = ObservationModel.objects.all().filter(
                        encounter_identifier=encounter_identifier, service_identifier=service_instance.service_identifier)
                    if service_observations:
                        for observation_instance in service_observations:
                            put_observation = None
                            post_observation = None
                            observation = {}
                            observation['identifier'] = observation_instance.observation_identifier
                            observation['status'] = observation_instance.observation_status
                            observation['code'] = observation_instance.observation_code
                            observation['category'] = observation_instance.observation_category
                            observation['effective'] = observation_instance.observation_effective.strftime(
                                '%Y-%m-%dT%H:%M:%S+07:00')
                            observation['value_quantity'] = observation_instance.observation_value_quantity
                            observation['value_unit'] = observation_instance.observation_value_unit
                            observation['reference_range'] = observation_instance.observation_reference_range
                            observation['performer'] = {}
                            observation['performer']['id'] = service_performer_id['id']
                            observation['performer']['name'] = service_instance.service_performer
                            get_observation = dt.query_observation(
                                observation['identifier'], query_type='id')
                            if get_observation:
                                observation['id'] = get_observation['id']
                            observation_data = dt.create_observation_resource(
                                observation, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                            test_observation = requests.post(fhir_server + '/Observation/$validate', headers={                                
                                'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                            print(test_observation.content.decode('utf-8'))
                            if get_observation:
                                put_observation = requests.put(fhir_server + "/Observation/" + get_observation['id'], headers={
                                    'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                                if put_observation.status_code == 200:
                                    observation_resource = ET.fromstring(
                                        put_observation.content.decode('utf-8'))

                                    observation_meta = dt.get_observation(
                                        observation_resource, query_type='meta')
                                else:
                                    print("có lỗi khi lưu observation")
                            else:
                                post_observation = requests.post(fhir_server + "/Observation/", headers={
                                    'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                                if post_observation.status_code == 201:
                                    observation_resource = ET.fromstring(
                                        post_observation.content.decode('utf-8'))

                                    observation_meta = dt.get_observation(
                                        observation_resource, query_type='meta')
                                else:
                                    print("có lỗi khi lưu observation")
                            observation_instance.observation_version = observation_meta['version']
                            observation_instance.save()
                    procedures = ProcedureModel.objects.filter(
                        service_identifier=service_instance)
                    if procedures:
                        for procedure_instance in procedures:
                            put_procedure = None
                            post_procedure = None
                            procedure = {}
                            procedure['identifier'] = procedure_instance.procedure_identifier
                            procedure['status'] = procedure_instance.procedure_status
                            procedure['category'] = procedure_instance.procedure_category
                            procedure['code'] = procedure_instance.procedure_code
                            if procedure_instance.procedure_performed_datetime:
                                procedure['performed_datetime'] = procedure_instance.procedure_performed_datetime.strftime(
                                    '%Y-%m-%dT%H:%M:%S+07:00')
                            procedure['reasonCode'] = procedure_instance.procedure_reason_code
                            procedure['outcome'] = procedure_instance.procedure_outcome
                            procedure['complication'] = procedure_instance.procedure_complication
                            procedure['follow_up'] = procedure_instance.procedure_follow_up
                            procedure['note'] = procedure_instance.procedure_note
                            procedure['used'] = procedure_instance.procedure_used
                            procedure['performer'] = {}
                            procedure['performer']['id'] = service_performer_id['id']
                            procedure['performer']['name'] = service_instance.service_performer
                            procedure['reason_code'] = procedure_instance.procedure_reason_code
                            get_procedure = dt.query_procedure(
                                procedure['identifier'], query_type='id')
                            if get_procedure:
                                procedure['id'] = get_procedure['id']
                            procedure_data = dt.create_procedure_resource(
                                procedure, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                            test_procedure = requests.post(fhir_server + '/Procedure/$validate', headers={                                
                                'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                            print(test_procedure.content.decode('utf-8'))
                            if get_procedure:
                                put_procedure = requests.put(fhir_server + "/Procedure/" + get_procedure['id'], headers={
                                    'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                                if put_procedure.status_code == 200:
                                    procedure_resource = ET.fromstring(
                                        put_procedure.content.decode('utf-8'))
                                    procedure_meta = dt.get_procedure(
                                        procedure_resource, query_type='meta')
                                else:
                                    print("có lỗi khi lưu procedủe")
                            else:
                                post_procedure = requests.post(fhir_server + "/Procedure/", headers={
                                    'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                                if post_procedure.status_code == 201:
                                    procedure_resource = ET.fromstring(
                                        post_procedure.content.decode('utf-8'))

                                    procedure_meta = dt.get_procedure(
                                        procedure_resource, query_type='meta')
                                else:
                                    print("có lỗi khi lưu procedure")
                            procedure_instance.procedure_version = procedure_meta['version']
                            procedure_instance.save()
                    try:
                        diagnostic_report_instance = DiagnosticReportModel.objects.get(encounter_identifier=encounter_instance,
                                                                                       service_identifier=service_instance)
                        put_diagnostic_report = None
                        post_diagnostic_report = None
                        diagnostic_report = {}
                        diagnostic_report['identifier'] = diagnostic_report_instance.diagnostic_identifier
                        diagnostic_report['status'] = diagnostic_report_instance.diagnostic_status
                        diagnostic_report['category'] = diagnostic_report_instance.diagnostic_category
                        diagnostic_report['code'] = diagnostic_report_instance.diagnostic_code
                        diagnostic_report['effective'] = diagnostic_report_instance.diagnostic_effective.strftime(
                            '%Y-%m-%dT%H:%M:%S+07:00')
                        diagnostic_report['conclusion'] = diagnostic_report_instance.diagnostic_conclusion
                        diagnostic_report['performer'] = {}
                        diagnostic_report['performer']['id'] = service_performer_id['id']
                        diagnostic_report['performer']['name'] = service_instance.service_performer_identifier.name
                        get_diagnostic_report = dt.query_diagnostic_report(
                            diagnostic_report['identifier'], query_type='id')
                        if get_diagnostic_report:
                            diagnostic_report['id'] = get_diagnostic_report['id']
                        diagnostic_report_data = dt.create_diagnostic_report_resource(
                            diagnostic_report, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                        test_diagnostic_report = requests.post(fhir_server + '/DiagnosticReport/$validate', headers={                            
                            'Content-type': 'application/xml'}, data=diagnostic_report_data.decode('utf-8'))
                        print(test_diagnostic_report.content.decode('utf-8'))
                        if get_diagnostic_report:
                            put_diagnostic_report = requests.put(fhir_server + '/DiagnosticReport/' + diagnostic_report['id'], headers={
                                'Content-type': 'application/xml'}, data=diagnostic_report_data.decode('utf-8'))
                            if put_diagnostic_report.status_code == 200:
                                diagnostic_report_resource = ET.fromstring(
                                    put_diagnostic_report.content.decode('utf-8'))

                                diagnostic_report_meta = dt.get_diagnostic_report(
                                    diagnostic_report_resource, query_type='meta')
                            else:
                                print("có lỗi khi lưu diagnostic report")
                        else:
                            post_diagnostic_report = requests.post(fhir_server + '/DiagnosticReport/', headers={
                                'Content-type': 'application/xml'}, data=diagnostic_report_data.decode('utf-8'))
                            if post_diagnostic_report.status_code == 201:
                                diagnostic_report_resource = ET.fromstring(
                                    post_diagnostic_report.content.decode('utf-8'))
                                diagnostic_report_meta = dt.get_diagnostic_report(
                                    diagnostic_report_resource, query_type='meta')
                            else:
                                print("có lỗi khi lưu diagnostic report")
                        diagnostic_report_instance.diagnostic_version = diagnostic_report_meta[
                            'version']
                        diagnostic_report_instance.save()
                    except DiagnosticReportModel.DoesNotExist:
                        pass
                else:
                    pass
            observation_instances = ObservationModel.objects.all().filter(
                encounter_identifier=encounter_instance, observation_category='vital-signs')
            for observation_instance in observation_instances:
                put_observation = None
                post_observation = None
                observation = {}
                observation['identifier'] = observation_instance.observation_identifier
                observation['status'] = observation_instance.observation_status
                observation['code'] = observation_instance.observation_code
                observation['category'] = observation_instance.observation_category
                observation['effective'] = observation_instance.observation_effective.strftime(
                    '%Y-%m-%dT%H:%M:%S+07:00')
                observation['value_quantity'] = observation_instance.observation_value_quantity
                observation['value_unit'] = observation_instance.observation_value_unit
                observation['performer'] = {}
                observation['performer']['id'] =  participant_id['id']
                observation['performer']['name'] = participant.name              
                get_observation = dt.query_observation(
                    observation['identifier'], query_type='id')
                if get_observation:
                    observation['id'] = get_observation['id']
                observation_data = dt.create_observation_resource(
                    observation, patient['id'], patient['name'], encounter['id'])
                test_observation = requests.post(fhir_server + '/Observation/$validate', headers={                                
                                'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                print(test_observation.content.decode('utf-8'))
                if get_observation:
                    put_observation = requests.put(fhir_server + "/Observation/" + get_observation['id'], headers={
                        'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                    if put_observation.status_code == 200:
                        observation_resource = ET.fromstring(
                            put_observation.content.decode('utf-8'))
                        observation_meta = dt.get_observation(
                            observation_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu observation")
                else:
                    post_observation = requests.post(fhir_server + "/Observation/", headers={
                        'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                    if post_observation.status_code == 201:
                        observation_resource = ET.fromstring(
                            post_observation.content.decode('utf-8'))
                        observation_meta = dt.get_observation(
                            observation_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu observation")
                observation_instance.observation_version = observation_meta['version']
                observation_instance.save()
            medication_instances = MedicationModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            for medication_instance in medication_instances:
                put_medication = None
                post_medication = None
                medication = {}
                medication['identifier'] = medication_instance.medication_identifier
                medication['status'] = medication_instance.medication_status
                medication['medication'] = medication_instance.medication_medication
                medication['effective'] = medication_instance.medication_effective.strftime(
                    '%Y-%m-%d')
                medication['date_asserted'] = medication_instance.medication_date_asserted.strftime(
                    '%Y-%m-%d')
                medication['reason_code'] = medication_instance.medication_reason_code
                medication['additional_instruction'] = medication_instance.dosage_additional_instruction
                medication['patient_instruction'] = medication_instance.dosage_patient_instruction
                medication['frequency'] = str(
                    medication_instance.dosage_frequency)
                medication['period'] = str(medication_instance.dosage_period) + \
                    ' ' + medication_instance.dosage_period_unit
                medication['duration'] = str(medication_instance.dosage_duration) + \
                    ' ' + medication_instance.dosage_duration_unit
                medication['when'] = medication_instance.dosage_when
                medication['offset'] = medication_instance.dosage_offset
                medication['route'] = medication_instance.dosage_route
                medication['quantity'] = str(
                    medication_instance.dosage_quantity) + ' ' + medication_instance.dosage_quantity_unit
                get_medication = dt.query_medication(
                    medication['identifier'], query_type='id')
                if get_medication:
                    medication['id'] = get_medication['id']
                medication_data = dt.create_medication_resource(
                    medication, patient['id'], patient['name'], encounter['id'])
                test_medication = requests.post(fhir_server + '/MedicationStatement/$validate', headers={                    
                    'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                print(test_medication.content.decode('utf-8'))
                if get_medication:
                    put_medication = requests.put(fhir_server + "/MedicationStatement/" + get_medication['id'], headers={
                        'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                    # print(put_medication.status_code)
                    if put_medication.status_code == 200:
                        medication_resource = ET.fromstring(
                            put_medication.content.decode('utf-8'))

                        medication_meta = dt.get_observation(
                            medication_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu medication")
                else:
                    post_medication = requests.post(fhir_server + "/MedicationStatement/", headers={
                        'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                    # print(post_medication.status_code)
                    # print(post_medication.content.decode('utf-8'))
                    if post_medication.status_code == 201:
                        medication_resource = ET.fromstring(
                            post_medication.content.decode('utf-8'))
                        medication_meta = dt.get_observation(
                            medication_resource, query_type='meta')
                    else:
                        print("có lỗi khi lưu medication")
                medication_instance.medication_version = medication_meta['version']
                medication_instance.save()
            encounter_instance.encounter_sharing_status = True
            encounter_instance.save()
            print(encounter_instance)
            messages.success(request, "Lưu thành công")
            return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
        else:
            messages.error(request, "Xảy ra lỗi trong quá trình lưu")
            return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)


def delete(request):
    if request.method == "POST":
        if not request.POST.get('resource_type') or not request.POST.get('url_next'):
            messages.error(request, "Yêu cầu không hợp lệ")
            return HttpResponseRedirect('/')
        resource_type = request.POST['resource_type']
        resource_identifier = request.POST.get('resource_identifier')
        url_next = request.POST['url_next']
        if resource_type == 'condition':
            try:
                resource = ConditionModel.objects.get(
                    condition_identifier=resource_identifier)
                if request.user.username == resource.encounter_identifier.encounter_participant_identifier.identifier:
                    resource.delete()
            except:
                messages.error(request, "Tài nguyên không tồn tại")
        elif resource_type == 'observation':
            try:
                resource = ObservationModel.objects.get(
                    observation_identifier=resource_identifier)
                if request.user.role == 'medical laboratory technician':
                    resource.delete()
            except:
                messages.error(request, "Tài nguyên không tồn tại")
        elif resource_type == 'medication_statement':
            try:
                resource = MedicationModel.objects.get(
                    medication_identifier=resource_identifier)
                if request.user.username == resource.encounter_identifier.encounter_participant_identifier.identifier:
                    resource.delete()
            except:
                messages.error(request, "Tài nguyên không tồn tại")
        elif resource_type == 'service_request':
            try:
                resource = ServiceRequestModel.objects.get(
                    service_identifier=resource_identifier)
                if request.user.username == resource.encounter_identifier.encounter_participant_identifier.identifier:
                    resource.delete()
            except:
                messages.error(request, "Tài nguyên không tồn tại")
        elif resource_type == 'allergy':
            try:
                resource = AllergyModel.objects.get(
                    allergy_identifier=resource_identifier)
                if request.user.username == resource.encounter_identifier.encounter_participant_identifier.identifier:
                    resource.delete()
            except:
                messages.error(request, "Tài nguyên không tồn tại")
        elif resource_type == 'schedule_value':
            practitioner = PractitionerModel.objects.get(
                identifier=request.user.username)
            print(request.POST)
            try:
                value = Schedule.objects.get(practitioner_name=practitioner.name, practitioner_identifier=practitioner,
                                             schedule_date=request.POST['delete_date'], session=request.POST['delete_session'])
                encounters = AssignedEncounter.objects.filter(practitioner_identifier=practitioner, encounter_date=request.POST['delete_date'], session=request.POST['delete_session']).exclude(assigned_encounter__encounter_status='finished')
                if encounters.count() == 0:
                    value.delete()
                else: 
                    messages.error(request, "Bạn đang có lịch khám chưa hoàn tất")
            except Exception as e:
                print(e)
                messages.error(request, "Dữ liệu không tồn tại")
        elif resource_type == 'sharing_encounter':
            try:
                encounter = EncounterModel.objects.get(
                    encounter_identifier=resource_identifier)
            except:
                messages.error(request, "Tài nguyên không tồn tại")
                return HttpResponseRedirect(url_next)
            if encounter.encounter_storage == 'hapi':
                messages.error(request, "Tài nguyên không tồn tại")
                return HttpResponseRedirect(url_next)
            try:
                connection_test = requests.get(fhir_server + "/Patient")
                if connection_test.status_code != 200:
                    messages.error(
                        request, "Không thể kết nối với kho FHIR, vui lòng liên hệ kĩ thuật viên")
                    return HttpResponseRedirect(url_next)
            except:
                messages.error(
                    request, "Kho FHIR không hoạt động, không thể ngừng chia sẻ tài nguyên")
                return HttpResponseRedirect(url_next)
            get_encounter = requests.get(fhir_server + "/Encounter?identifier=urn:trinhcongminh|" +
                                            encounter.encounter_identifier, headers={'Content-type': 'application/xml'})
            if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
                observations = ObservationModel.objects.filter(
                    encounter_identifier=resource_identifier)
                service_requests = ServiceRequestModel.objects.filter(
                    encounter_identifier=resource_identifier)
                diagnostic_reports = DiagnosticReportModel.objects.filter(
                    encounter_identifier=resource_identifier)
                conditions = ConditionModel.objects.filter(
                    encounter_identifier=resource_identifier)
                allergies = AllergyModel.objects.filter(
                    encounter_identifier=resource_identifier)
                procedures = ProcedureModel.objects.filter(
                    encounter_identifier=resource_identifier)
                medication_statements = MedicationModel.objects.filter(
                    encounter_identifier=resource_identifier)
                for observation in observations:
                    delete_resource = requests.delete(fhir_server + "/Observation?identifier=urn:trinhcongminh|" +
                                                      observation.observation_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for diagnostic_report in diagnostic_reports:
                    delete_resource = requests.delete(fhir_server + "/DiagnosticReport?identifier=urn:trinhcongminh|" +
                                                      diagnostic_report.diagnostic_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for condition in conditions:
                    delete_resource = requests.delete(fhir_server + "/Condition?identifier=urn:trinhcongminh|" +
                                                      condition.condition_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for procedure in procedures:
                    delete_resource = requests.delete(fhir_server + "/Procedure?identifier=urn:trinhcongminh|" +
                                                      procedure.procedure_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for allergy in allergies:
                    delete_resource = requests.delete(fhir_server + "/AllergyIntolerance?identifier=urn:trinhcongminh|" +
                                                      allergy.allergy_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for medication_statement in medication_statements:
                    delete_resource = requests.delete(fhir_server + "/MedicationStatement?identifier=urn:trinhcongminh|" +
                                                      medication_statement.medication_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                for service_request in service_requests:
                    delete_resource = requests.delete(fhir_server + "/ServiceRequest?identifier=urn:trinhcongminh|" +
                                                      service_request.service_identifier, headers={'Content-type': 'application/xml'})
                    if delete_resource.status_code != 200:
                        print(delete_resource.content.decode('utf-8'))
                delete_resource = requests.delete(fhir_server + "/Encounter?identifier=urn:trinhcongminh|" +
                                                  encounter.encounter_identifier, headers={'Content-type': 'application/xml'})
                if delete_resource.status_code == 200:
                    encounter.encounter_sharing_status = False
                    encounter.save()
                else:
                    messages.error(
                        request, "Gặp lỗi trong quá trình ngừng chia sẻ")
            else:
                messages.error(request, "Tài nguyên đang không được chia sẻ")
        return HttpResponseRedirect(url_next)


class view_benhan(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier},
                'Observation': {}}
        patient = PatientModel.objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        encounter_history = []
        # if encounter.encounter_version > 1:
        #     encounter_id = dt.query_encounter(encounter_identifier, query_type='id')['id']
        #     for i in range(encounter.encounter_version-1, 0, -1):
        #         encounter_history.append(dt.query_encounter_history(encounter_id, str(i), query_type='all'))
        admission_conditions = {'patient': [], 'doctor': {'toanthan': [], 'tuanhoan': [], 'hohap': [
        ], 'tieuhoa': [], 'tts': [], 'thankinh': [], 'cxk': [], 'tmh': [], 'rhm': [], 'mat': [], 'noitiet': []}}
        resolved_conditions = []
        conditions_history = {}
        observations_history = {}
        discharge_conditions = []
        comorbidity_conditions = []
        other_conditions = []
        diagnostic_reports = []
        diagnostic_reports_history = {}
        allergies = []
        allergies_history = {}
        condition_displays = {}
        if encounter.encounter_storage == 'local':
            resolved_conditions = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='resolved condition by patient')
            admission_conditions['patient'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by patient')
            admission_conditions['doctor']['toanthan'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='toanthan')
            admission_conditions['doctor']['tuanhoan'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='tuanhoan')
            admission_conditions['doctor']['hohap'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='hohap')
            admission_conditions['doctor']['tieuhoa'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='tieuhoa')
            admission_conditions['doctor']['tts'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='tts')
            admission_conditions['doctor']['thankinh'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='thankinh')
            admission_conditions['doctor']['cxk'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='cxk')
            admission_conditions['doctor']['tmh'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='tmh')
            admission_conditions['doctor']['rhm'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='rhm')
            admission_conditions['doctor']['mat'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='mat')
            admission_conditions['doctor']['noitiet'] = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='admission condition by doctor', condition_category='noitiet')
            discharge_conditions = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='discharge condition by doctor')
            for condition in discharge_conditions:
                if ' ' in condition.condition_code:
                    condition_displays[condition.condition_identifier] = ""
                    codes = condition.condition_code.split(' ')
                    for code in codes:
                        disease = DischargeDisease.objects.get(
                            disease_code=code)
                        condition_displays[condition.condition_identifier] = (
                            condition_displays[condition.condition_identifier] + ' ' + disease.disease_name).strip()
                else:
                    condition_displays[condition.condition_identifier] = ""
                    disease = DischargeDisease.objects.get(
                        disease_code=condition.condition_code)
                    condition_displays[condition.condition_identifier] += ' ' + \
                        disease.disease_name
            comorbidity_conditions = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='comorbidity condition by doctor')
            conditions = ConditionModel.objects.filter(
                encounter_identifier=encounter)
            # for condition in conditions:
            #     conditions_history[condition.condition_identifier] = []
            #     if condition.condition_version > 1:
            #         condition_id = dt.query_condition(condition.condition_identifier, query_type='id')['id']
            #         for i in range(condition.condition_version-1, 0, -1):
            #             conditions_history[condition.condition_identifier].append(dt.query_condition_history(condition_id, str(i), query_type='all'))
            observations = ObservationModel.objects.all().filter(
                encounter_identifier=encounter_identifier, observation_category='vital-signs')
            for observation in observations:
                if observation.observation_code.lower() == 'mạch':
                    data['Observation']['mach'] = observation
                elif observation.observation_code.lower() == 'nhiệt độ':
                    data['Observation']['nhietdo'] = observation
                elif observation.observation_code.lower() == 'nhịp thở':
                    data['Observation']['nhiptho'] = observation
                elif observation.observation_code.lower() == 'cân nặng':
                    data['Observation']['cannang'] = observation
                elif observation.observation_code.lower() == 'huyết áp tâm thu':
                    data['Observation']['tamthu'] = observation
                elif observation.observation_code.lower() == 'huyết áp tâm trương':
                    data['Observation']['tamtruong'] = observation
                # if observation.observation_version != 0 and observation.observation_version > 1:
                #     observation_id = dt.query_observation(observation.observation_identifier, query_type='id')['id']
                #     observations_history[observation.observation_identifier] = []
                #     for i in range(observation.observation_version-1, 0, -1):
                #         observations_history[observation.observation_identifier].append(dt.query_observation_history(observation_id, str(i), query_type='all'))
            diagnostic_reports = DiagnosticReportModel.objects.filter(
                encounter_identifier=encounter)
            # for diagnostic_report in diagnostic_reports:
            #     if diagnostic_report.diagnostic_version > 1:
            #         diagnostic_id = dt.query_diagnostic_report(diagnostic_report.diagnostic_identifier, query_type='id')
            #         diagnostic_reports_history[diagnostic_report.diagnostic_identifier] = []
            #         for i in range(diagnostic_report.diagnostic_version, 0, -1):
            #             diagnostic_reports_history[diagnostic_report.diagnostic_identifier].append(dt.query_diagnostic_report_history(diagnostic_id, str(i), query_type='all'))
            allergies = AllergyModel.objects.all().filter(encounter_identifier=encounter)
            # for allergy in allergies:
            #     if allergy.allergy_version > 1:
            #         allergy_id = dt.query_allergy(allergy.allergy_identifier, query_type='id')['id']
            #         allergies_history[allergy.allergy_identifier] = []
            #         for i in range(allergy.allergy_version, 0 ,-1):
            #             allergies_history[allergy.allergy_identifier].append(dt.query_allergy_history(allergy_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
            try:
                connection_test = requests.get(fhir_server + "/Patient")
                if connection_test.status_code != 200:
                    messages.error(
                        request, "Không thể kết nối tới kho FHIR, vui lòng liên hệ kĩ thuật viên")
                    return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            except:
                messages.error(request, "Kho FHIR không hoạt động")
                return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            get_condition = requests.get(fhir_server + "/Condition?encounter.identifier=urn:trinhcongminh|" +
                                         encounter_identifier, headers={'Content-type': 'application/xml'})
            if get_condition.status_code == 200 and 'entry' in get_condition.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_condition.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    condition = {}
                    resource = entry.find('d:resource', ns)
                    condition_resource = resource.find('d:Condition', ns)
                    condition_identifier = condition_resource.find(
                        'd:identifier', ns)
                    condition_identifier_value = condition_identifier.find(
                        'd:value', ns).attrib['value']
                    condition = dt.query_condition(
                        condition_identifier_value, query_type='all')
                    if condition['condition_note'] == 'admission condition by patient':
                        admission_conditions['patient'].append(condition)
                    elif condition['condition_note'] == 'resolved condition by patient':
                        resolved_conditions.append(condition)
                    elif condition['condition_note'] == 'admission condition by doctor':
                        admission_conditions['doctor'][condition['condition_category']].append(
                            condition)
                    elif condition['condition_note'] == 'discharge condition by doctor':
                        discharge_conditions.append(condition)
                    elif condition['condition_note'] == 'comorbidity condition by doctor':
                        comorbidity_conditions.append(condition)
                    else:
                        other_conditions.append(condition)
                    # if int(condition['version']) > 1:
                    #     conditions_history[condition['condition_identifier']] = []
                    #     for i in range(int(condition['version'])-1, 0, -1):
                    #         conditions_history[condition['condition_identifier']].append(dt.query_condition_history(condition['id'], str(i), query_type='all'))
            get_observations = requests.get(fhir_server + "/Observation?encounter.identifier=urn:trinhcongminh|" +
                                            encounter_identifier + "&category:text=vital-signs", headers={'Content-type': 'application/xml'})
            if get_observations.status_code == 200 and 'entry' in get_observations.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_observations.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    observation = {}
                    resource = entry.find('d:resource', ns)
                    observation_resource = resource.find(
                        'd:Observation', ns)
                    observation_identifier = observation_resource.find(
                        'd:identifier', ns)
                    observation = dt.query_observation(observation_identifier.find(
                        'd:value', ns).attrib['value'], query_type='all')
                    if observation['observation_code'] == 'mạch':
                        data['Observation']['mach'] = observation
                    elif observation['observation_code'] == 'nhiệt độ':
                        data['Observation']['nhietdo'] = observation
                    elif observation['observation_code'] == 'nhịp thở':
                        data['Observation']['nhiptho'] = observation
                    elif observation['observation_code'] == 'cân nặng':
                        data['Observation']['cannang'] = observation
                    elif observation['observation_code'] == 'huyết áp tâm thu':
                        data['Observation']['tamthu'] = observation
                    elif observation['observation_code'] == 'huyết áp tâm trương':
                        data['Observation']['tamtruong'] = observation
                    # if int(observation['version']) > 1:
                    #     observations_history[observation['observation_identifier']] = []
                    #     for i in range(int(observation['version'])-1, 0 , -1):
                    #         observations_history[observation['observation_identifier']].append(dt.query_observation_history(observation['id'], str(i), query_type='all'))
            get_allergies = requests.get(fhir_server + "/AllergyIntolerance?encounter.identifier=urn:trinhcongminh|" +
                                         encounter_identifier, headers={'Content-type': 'application/xml'})
            if get_allergies.status_code == 200 and 'entry' in get_allergies.content.decode('utf-8'):
                get_root = ET.fromstring(get_allergies.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    allergy = {}
                    resource = entry.find('d:resource', ns)
                    allergy_resource = resource.find(
                        'd:AllergyIntolerance', ns)
                    allergy_identifier = allergy_resource.find(
                        'd:identifier', ns)
                    allergy_identifier_value = allergy_identifier.find(
                        'd:value', ns).attrib['value']
                    allergy = dt.query_allergy(
                        allergy_identifier_value, query_type='all')
                    allergies.append(allergy)
                    # if int(allergy['version']) > 1:
                    #     allergies_history[allergy['allergy_history']] = []
                    #     for i in range(int(allergy['version']), 0, -1):
                    #         allergies_history[allergy['allergy_history']].append(dt.query_allergy_history(allergy['id'], str(i), query_type='all'))
            get_diagnostic_reports = requests.get(fhir_server + "/DiagnosticReport?encounter.identifier=urn:trinhcongminh|" +
                                                  encounter_identifier, headers={'Content-type': 'application/xml'})
            if get_diagnostic_reports.status_code == 200 and 'entry' in get_diagnostic_reports.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_diagnostic_reports.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    diagnostic_report = {}
                    resource = entry.find('d:resource', ns)
                    diagnostic_report_resource = resource.find(
                        'd:DiagnosticReport', ns)
                    diagnostic_report_identifier = diagnostic_report_resource.find(
                        'd:identifier', ns)
                    diagnostic_report_identifier_value = diagnostic_report_identifier.find(
                        'd:value', ns).attrib['value']
                    diagnostic_report = dt.query_diagnostic_report(
                        diagnostic_report_identifier_value, query_type='all')
                    diagnostic_reports.append(diagnostic_report)
        context = {
            'data': data,
            'patient': patient,
            'encounter': encounter,
            'encounter_history': encounter_history,
            'admission_conditions': admission_conditions,
            'resolved_conditions': resolved_conditions,
            'discharge_conditions': discharge_conditions,
            'comorbidity_conditions': comorbidity_conditions,
            'other_conditions': other_conditions,
            'allergies': allergies,
            'conditions_history': conditions_history,
            'observations_history': observations_history,
            'diagnostic_reports': diagnostic_reports,
            'allergies_history': allergies_history,
            'condition_displays': condition_displays,
            'condition_severity': CONDITION_SEVERITY_CHOICES,
            'allergy_criticality': ALLERGY_CRITICALITY_CHOICES,
            'allergy_severity': ALLERGY_SEVERITY_CHOICES,
            'relationship': CONTACT_RELATIONSHIP_CHOICES
        }
        return render(request, 'fhir/view/benhan.html', context)


class view_xetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier},
                'Observation': {}}
        patient = PatientModel.objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = []
        observations = {}
        services_history = {}
        observations_history = {}
        if encounter.encounter_storage == 'local':
            services = ServiceRequestModel.objects.filter(
                encounter_identifier=encounter, service_category='Laboratory procedure')
            for service in services:
                if service.service_version > 1:
                    services_history[service.service_identifier] = []
                    service_id = dt.query_service(
                        service.service_identifier, query_type='id')['id']
                    # for i in range(service.service_version-1, 0, -1):
                    #     services_history[service.service_identifier].append(dt.query_service_history(service_id, str(i), query_type='all'))
                observations[service.service_identifier] = ObservationModel.objects.filter(
                    encounter_identifier=encounter, service_identifier=service)
                for observation in observations[service.service_identifier]:
                    if observation.observation_version > 1:
                        observations_history[observation.observation_identifier] = [
                        ]
                        observation_id = dt.query_observation(
                            observation.observation_identifier, query_type='id')['id']
                        # for i in range(observation.observation_version-1, 0, -1):
                        #     observations_history[observation.observation_identifier].append(dt.query_observation_history(observation_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
            try:
                connection_test = requests.get(fhir_server + "/Patient")
                if connection_test.status_code != 200:
                    messages.error(
                        request, "Không thể kết nối tới kho FHIR, vui lòng liên hệ kĩ thuật viên")
                    return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            except:
                messages.error(request, "Kho FHIR không hoạt động")
                return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            get_services = requests.get(fhir_server + '/ServiceRequest?encounter.identifier=urn:trinhcongminh|' +
                                        encounter_identifier + '&category:text=Laboratory procedure',  headers={'Content-type': 'application/xml'})
            if get_services.status_code == 200 and 'entry' in get_services.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_services.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    service = {}
                    resource = entry.find('d:resource', ns)
                    service_resource = resource.find(
                        'd:ServiceRequest', ns)
                    service_identifier = service_resource.find(
                        'd:identifier', ns)
                    service = dt.query_service(service_identifier.find(
                        'd:value', ns).attrib['value'], query_type='all')

                    # if int(service['version']) > 1:
                    #     services_history[service['service_identifier']] = []
                    #     for i in range(int(service['version'])-1, 0, -1):
                    #         services_history[service['service_identifier']].append(dt.query_service_history(service['id'], str(i), query_type='all'))
                    observations[service['service_identifier']] = []
                    service_observations = requests.get(fhir_server + "/Observation?based-on.identifier=urn:trinhcongminh|" +
                                                        service['service_identifier'], headers={'Content-type': 'application/xml'})
                    if service_observations.status_code == 200 and 'entry' in service_observations.content.decode('utf-8'):
                        get_root = ET.fromstring(
                            service_observations.content.decode('utf-8'))
                        for entry in get_root.findall('d:entry', ns):
                            observation = {}
                            resource = entry.find('d:resource', ns)
                            observation_resource = resource.find(
                                'd:Observation', ns)
                            observation_identifier = observation_resource.find(
                                'd:identifier', ns)
                            observation = dt.query_observation(observation_identifier.find(
                                'd:value', ns).attrib['value'], query_type='all')
                            observations[service['service_identifier']].append(
                                observation)
                        print(
                            observations[service['service_identifier']][-1].get('observation_effective'))
                        service['service_performed_date'] = observations[service['service_identifier']
                                                                         ][-1].get('observation_effective')
                        print(service)
                        # if int(observation['version']) > 1:
                        #     observations_history[observation['observation_identifier']] = []
                        #     for i in range(int(observation['version'])-1, 0, -1):
                        #         observations_history[observation['observation_identifier']].append(dt.query_observation_history(observation['id'], str(i), query_type='all'))
                    services.append(service)
        context = {
            'data': data,
            'patient': patient,
            'encounter': encounter,
            'services': services,
            'observations': observations,
            'services_history': services_history,
            'observations_history': observations_history
        }
        return render(request, 'fhir/view/phieuxetnghiem.html', context)


class view_thuthuat(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor" and request.user.role != "medical assistant":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        patient = PatientModel.objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = []
        procedures = {}
        diagnostic_reports = {}
        services_history = {}
        procedures_history = {}
        diagnostic_reports_history = {}
        images = {}
        if encounter.encounter_storage == 'local':
            services = ServiceRequestModel.objects.filter(
                encounter_identifier=encounter, service_category='Imaging')
            for service in services:
                if service.service_version > 1:
                    services_history[service.service_identifier] = []
                    service_id = dt.query_service(
                        service.service_identifier, query_type='id')['id']
                    # for i in range(service.service_version-1, 0 ,-1):
                    #     services_history[service.service_identifier].append(dt.query_condition_history(service_id, str(i), query_type='all'))
                procedures[service.service_identifier] = ProcedureModel.objects.filter(
                    encounter_identifier=encounter, service_identifier=service)
                for procedure in procedures[service.service_identifier]:
                    images[procedure.procedure_identifier] = ImageResult.objects.filter(procedure_identifier=procedure)
                    if procedure.procedure_version > 1:
                        procedures_history[procedure.procedure_identifier] = []
                        procedure_id = dt.query_procedure(
                            procedure.procedure_identifier, query_type='id')['id']
                        # for i in range(procedure.procedure_version-1, 0 ,-1):
                        #     procedures_history[procedure.procedure_identifier].append(dt.query_procedure_history(procedure_id, str(i), query_type='all'))
                diagnostic_reports[service.service_identifier] = DiagnosticReportModel.objects.filter(
                    encounter_identifier=encounter, service_identifier=service)
                for diagnostic_report in diagnostic_reports[service.service_identifier]:
                    if diagnostic_report.diagnostic_version > 1:
                        diagnostic_reports_history[diagnostic_report.diagnostic_identifier] = [
                        ]
                        diagnostic_report_id = dt.query_diagnostic_report(
                            diagnostic_report.diagnostic_identifier, query_type='id')['id']
                        # for i in range(diagnostic_report.diagnostic_version-1, 0, -1):
                        #     diagnostic_reports_history[diagnostic_report.diagnostic_identifier].append(dt.query_diagnostic_report_history(diagnostic_report_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
            try:
                connection_test = requests.get(fhir_server + "/Patient")
                if connection_test.status_code != 200:
                    messages.error(
                        request, "Không thể kết nối tới kho FHIR, vui lòng liên hệ kĩ thuật viên")
                    return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            except:
                messages.error(request, "Kho FHIR không hoạt động")
                return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            get_services = requests.get(fhir_server + '/ServiceRequest?encounter.identifier=urn:trinhcongminh|' +
                                        encounter_identifier + '&category:text=Imaging',  headers={'Content-type': 'application/xml'})
            if get_services.status_code == 200 and 'entry' in get_services.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_services.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    service = {}
                    resource = entry.find('d:resource', ns)
                    service_resource = resource.find(
                        'd:ServiceRequest', ns)
                    service_identifier = service_resource.find(
                        'd:identifier', ns)
                    service = dt.query_service(service_identifier.find(
                        'd:value', ns).attrib['value'], query_type='all')

                    # if int(service['version']) > 1:
                    #     services_history[service['service_identifier']] = []
                    #     for i in range(int(service['version'])-1, 0, -1):
                    #         services_history[service['service_identifier']].append(dt.query_service_history(service['id'], str(i), query_type='all'))
                    procedures[service['service_identifier']] = []
                    get_procedures = requests.get(fhir_server + "/Procedure?based-on.identifier=urn:trinhcongminh|" +
                                                  service['service_identifier'], headers={'Content-type': 'application/xml'})
                    if get_procedures.status_code == 200 and 'entry' in get_procedures.content.decode('utf-8'):
                        get_root = ET.fromstring(
                            get_procedures.content.decode('utf-8'))
                        for entry in get_root.findall('d:entry', ns):
                            procedure = {}
                            resource = entry.find('d:resource', ns)
                            procedure_resource = resource.find(
                                'd:Procedure', ns)
                            procedure_identifier = procedure_resource.find(
                                'd:identifier', ns)
                            procedure = dt.query_procedure(procedure_identifier.find(
                                'd:value', ns).attrib['value'], query_type='all')
                            procedures[service['service_identifier']].append(
                                procedure)
                        service['service_performed_date'] = procedures[service['service_identifier']
                                                                       ][-1].get('procedure_performed_datetime')
                        # if int(procedure['version']) > 1:
                        #     procedures_history[procedure['procedure_identifier']] = []
                        #     for i in range(int(procedure['version'])-1, 0, -1):
                        #         procedures_history[procedure['procedure_identifier']].append(dt.query_procedure_history(service['id'], str(i), query_type='all'))
                    diagnostic_reports[service['service_identifier']] = []
                    get_diagnostic_reports = requests.get(fhir_server + '/DiagnosticReport?based-on.identifier=urn:trinhcongminh|' +
                                                          service['service_identifier'], headers={'Content-type': 'application/xml'})
                    if get_diagnostic_reports.status_code == 200 and 'entry' in get_diagnostic_reports.content.decode('utf-8'):
                        get_root = ET.fromstring(
                            get_diagnostic_reports.content.decode('utf-8'))
                        for entry in get_root.findall('d:entry', ns):
                            diagnostic_report = {}
                            resource = entry.find('d:resource', ns)
                            diagnostic_report_resource = resource.find(
                                'd:DiagnosticReport', ns)
                            identifier = diagnostic_report_resource.find(
                                'd:identifier', ns)
                            diagnostic_report = dt.query_diagnostic_report(
                                identifier.find('d:value', ns).attrib['value'], query_type='all')
                            diagnostic_reports[service['service_identifier']].append(
                                diagnostic_report)
                            # if int(diagnostic_report['version']) > 1:
                            #     diagnostic_reports_history[diagnostic_report['diagnostic_identifier']] = []
                            #     for i in range(int(diagnostic_report['version'])-1, 0, -1):
                            #         diagnostic_reports_history[diagnostic_report['diagnostic_identifier']].append(dt.query_diagnostic_report_history(diagnostic_report['id'], str(i), query_type='all'))
                    services.append(service)
        context = {
            'data': data,
            'patient': patient,
            'encounter': encounter,
            'services': services,
            'procedures': procedures,
            'diagnostic_reports': diagnostic_reports,
            'images': images,
            'services_history': services_history,
            'procedures_history': procedures_history,
            'diagnostic_reports_history': diagnostic_reports_history,

        }
        return render(request, 'fhir/view/phieuthuthuat.html', context)


class view_donthuoc(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "medical assistant" and request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        patient = PatientModel.objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        medications = []
        medications_history = {}
        if encounter.encounter_storage == 'local':
            medications = MedicationModel.objects.filter(
                encounter_identifier=encounter)
            for medication in medications:
                if medication.medication_version > 1:
                    medications_history[medication.medication_identifier] = []
                    medication_id = dt.query_medication(
                        medication.medication_identifier, query_type='id')['id']
                    # for i in range(medication.medication_version-1, 0, -1):
                    #     medications_history[medication.medication_identifier].append(dt.query_medication_history(medication_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
            try:
                connection_test = requests.get(fhir_server + "/Patient")
                if connection_test.status_code != 200:
                    messages.error(
                        request, "Không thể kết nối tới kho FHIR, vui lòng liên hệ kĩ thuật viên")
                    return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            except:
                messages.error(request, "Kho FHIR không hoạt động")
                return HttpResponseRedirect('/fhir/display_detail/' + patient_identifier)
            get_medication_statements = requests.get(fhir_server + "/MedicationStatement?context.identifier=urn:trinhcongminh|" +
                                                     encounter_identifier, headers={'Content-type': 'application/xml'})
            if get_medication_statements.status_code == 200 and 'entry' in get_medication_statements.content.decode('utf-8'):
                get_root = ET.fromstring(
                    get_medication_statements.content.decode('utf-8'))
                for entry in get_root.findall('d:entry', ns):
                    medication_statement = {}
                    resource = entry.find('d:resource', ns)
                    medication_resource = resource.find(
                        'd:MedicationStatement', ns)
                    medication_identifier = medication_resource.find(
                        'd:identifier', ns)
                    medication_statement = dt.query_medication(
                        medication_identifier.find('d:value', ns).attrib['value'], query_type='all')
                    medications.append(medication_statement)
                    # if int(medication_statement['version']) > 1:
                    #     medications_history[medication_statement['medication_identifier']] = []
                    #     for i in range(int(medication_statement['version'])-1, 0, -1):
                    #         medications_history[medication_statement['medication_identifier']].append(dt.query_medication_history(medication_statement['id'], str(i), query_type='all'))
        context = {
            'data': data,
            'patient': patient,
            'encounter': encounter,
            'medications': medications,
            'medications_history': medications_history,
            'when': DOSAGE_WHEN_CHOICES,
            'unit': DOSAGE_UNIT_CHOICES
        }
        return render(request, 'fhir/view/donthuoc.html', context)


class schedule(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "doctor":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, practitioner_identifier):
        practitioner = PractitionerModel.objects.get(
            identifier=practitioner_identifier)
        now = timezone.localtime(timezone.now()).date()
        if now.weekday() == 6:
            monday = now + timedelta(days=1)
        else:
            monday = now - timedelta(days=now.weekday())
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        thursday = monday + timedelta(days=3)
        friday = monday + timedelta(days=4)
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)
        print(type(monday))
        schedule_dates = {'Monday': {}, 'Tuesday': {}, 'Wednesday': {
        }, 'Thursday': {}, 'Friday': {}, 'Saturday': {}}
        try:
            schedule_dates['Monday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=monday, session="morning")
        except:
            pass
        try:
            schedule_dates['Monday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=monday, session="afternoon")
        except:
            pass
        try:
            schedule_dates['Tuesday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=tuesday, session="morning")
        except:
            pass
        try:
            schedule_dates['Tuesday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=tuesday, session="afternoon")
        except:
            pass
        try:
            schedule_dates['Wednesday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=wednesday, session="morning")
        except:
            pass
        try:
            schedule_dates['Wednesday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=wednesday, session="afternoon")
        except:
            pass
        try:
            schedule_dates['Thursday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=thursday, session="morning")
        except:
            pass
        try:
            schedule_dates['Thursday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=thursday, session="afternoon")
        except:
            pass
        try:
            schedule_dates['Friday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=friday, session="morning")
        except:
            pass
        try:
            schedule_dates['Friday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=friday, session="afternoon")
        except:
            pass
        try:
            schedule_dates['Saturday']['morning'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=saturday, session="morning")
        except:
            pass
        try:
            schedule_dates['Saturday']['afternoon'] = Schedule.objects.get(
                practitioner_name=practitioner.name, practitioner_identifier=practitioner, schedule_date=saturday, session="afternoon")
        except:
            pass
        days_of_week = {'Monday': {'date': monday, 'is_future': monday >= now}, 'Tuesday': {'date': tuesday, 'is_future': tuesday >= now}, 'Wednesday': {'date': wednesday, 'is_future': wednesday >=
                                                                                                                                                         now}, 'Thursday': {'date': thursday, 'is_future': thursday >= now}, 'Friday': {'date': friday, 'is_future': friday >= now}, 'Saturday': {'date': saturday, 'is_future': saturday >= now}}
        assigned_encounters = {'Monday': {}, 'Tuesday': {}, 'Wednesday': {
        }, 'Thursday': {}, 'Friday': {}, 'Saturday': {}}
        assigned_encounters['Monday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=monday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Tuesday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=tuesday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Wednesday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=wednesday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Thursday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=thursday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Friday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=friday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Saturday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=saturday, session='morning', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Monday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=monday, session='afternoon', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Tuesday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=tuesday, session='afternoon', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Wednesday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=wednesday, session='afternoon', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Thursday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=thursday, session='afternoon', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Friday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=friday, session='afternoon', assigned_encounter__encounter_status='assigned')
        assigned_encounters['Saturday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=saturday, session='afternoon', assigned_encounter__encounter_status='assigned')
        in_progress_encounters = {'Monday': {}, 'Tuesday': {}, 'Wednesday': {
        }, 'Thursday': {}, 'Friday': {}, 'Saturday': {}}
        in_progress_encounters['Monday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=monday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Tuesday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=tuesday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Wednesday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=wednesday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Thursday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=thursday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Friday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=friday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Saturday']['morning'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=saturday, session='morning', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Monday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=monday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Tuesday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=tuesday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Wednesday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=wednesday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Thursday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=thursday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Friday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=friday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        in_progress_encounters['Saturday']['afternoon'] = AssignedEncounter.objects.filter(
            practitioner_name=practitioner.name, practitioner_identifier=practitioner, encounter_date=saturday, session='afternoon', assigned_encounter__encounter_status='in-progress')
        context = {
            'schedule_dates': schedule_dates,
            'days_of_week': days_of_week,
            'assigned_encounters': assigned_encounters,
            'in_progress_encounters': in_progress_encounters
        }
        return render(request, 'fhir/schedule.html', context)

    def post(self, request, practitioner_identifier):
        practitioner = PractitionerModel.objects.get(
            identifier=practitioner_identifier)
        if request.POST.get('encounter_identifier'):
            encounter = EncounterModel.objects.get(encounter_identifier=request.POST['encounter_identifier'])
            encounter.encounter_start = timezone.localtime(timezone.now())
            encounter.encounter_status = 'in-progress'
            encounter.save()
            return HttpResponseRedirect('/fhir/encounter/' + encounter.patient.identifier + '/' + encounter.encounter_identifier + '/hanhchinh')
        else: 
            date = request.POST['day_of_work']
            session = request.POST['session']
            now = timezone.localtime(timezone.now()).date()
            if now.weekday() == 6:
                monday = now + timedelta(days=1)
            else:
                monday = now - timedelta(days=now.weekday())
            gap_days = int(date)
            if now > monday + timedelta(days=gap_days):
                messages.error(request, "Không thể đăng ký lịch cho ngày đã qua")
                return HttpResponseRedirect(self.request.path_info) 
            try:
                Schedule.objects.get(practitioner_name=practitioner.name, practitioner_identifier=practitioner,
                                    schedule_date=monday + timedelta(days=gap_days), session=session)
                messages.error(request, 'Bạn đã đăng ký lịch cho buổi này rồi')
            except Schedule.DoesNotExist:
                Schedule.objects.create(practitioner_name=practitioner.name, practitioner_identifier=practitioner,
                                        schedule_date=monday + timedelta(days=gap_days), session=session)
            return HttpResponseRedirect(self.request.path_info) 


class manage_schedule(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        departments = ClinicalDepartment.objects.filter(
            department_type='lâm sàng')
        now = timezone.localtime(timezone.now()).date()
        if now.weekday() == 6:
            monday = now + timedelta(days=1)
        else:
            monday = now - timedelta(days=now.weekday())
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        thursday = monday + timedelta(days=3)
        friday = monday + timedelta(days=4)
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)
        schedule_dates = {'Monday': {}, 'Tuesday': {}, 'Wednesday': {
        }, 'Thursday': {}, 'Friday': {}, 'Saturday': {}}
        assigned_encounters = {'Monday': {'morning': {}, 'afternoon': {}}, 'Tuesday': {'morning': {}, 'afternoon': {}}, 'Wednesday': {
            'morning': {}, 'afternoon': {}}, 'Thursday': {'morning': {}, 'afternoon': {}}, 'Friday': {'morning': {}, 'afternoon': {}}, 'Saturday': {'morning': {}, 'afternoon': {}}}
        if request.GET.get('department_schedule'):
            try:
                department = ClinicalDepartment.objects.get(
                    department_name=request.GET['department_schedule'])
                schedule_dates['Monday']['morning'] = Schedule.objects.filter(
                    schedule_date=monday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Monday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=monday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Tuesday']['morning'] = Schedule.objects.filter(
                    schedule_date=tuesday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Tuesday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=tuesday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Wednesday']['morning'] = Schedule.objects.filter(
                    schedule_date=wednesday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Wednesday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=wednesday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Thursday']['morning'] = Schedule.objects.filter(
                    schedule_date=thursday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Thursday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=thursday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Friday']['morning'] = Schedule.objects.filter(
                    schedule_date=friday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Friday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=friday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Saturday']['morning'] = Schedule.objects.filter(
                    schedule_date=saturday, session='morning', practitioner_identifier__department=request.GET['department_schedule'])
                schedule_dates['Saturday']['afternoon'] = Schedule.objects.filter(
                    schedule_date=saturday, session='afternoon', practitioner_identifier__department=request.GET['department_schedule'])

                for practitioner in schedule_dates['Monday']['morning']:
                    assigned_encounters['Monday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=monday, session='morning')
                for practitioner in schedule_dates['Monday']['afternoon']:
                    assigned_encounters['Monday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=monday, session='afternoon')
                for practitioner in schedule_dates['Tuesday']['morning']:
                    assigned_encounters['Tuesday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=tuesday, session='morning')
                for practitioner in schedule_dates['Tuesday']['afternoon']:
                    assigned_encounters['Tuesday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=tuesday, session='afternoon')
                for practitioner in schedule_dates['Wednesday']['morning']:
                    assigned_encounters['Wednesday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=wednesday, session='morning')
                for practitioner in schedule_dates['Wednesday']['afternoon']:
                    assigned_encounters['Wednesday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=wednesday, session='afternoon')
                for practitioner in schedule_dates['Thursday']['morning']:
                    assigned_encounters['Thursday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=thursday, session='morning')
                for practitioner in schedule_dates['Thursday']['afternoon']:
                    assigned_encounters['Thursday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=thursday, session='afternoon')
                for practitioner in schedule_dates['Friday']['morning']:
                    assigned_encounters['Friday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=friday, session='morning')
                for practitioner in schedule_dates['Friday']['afternoon']:
                    assigned_encounters['Friday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=friday, session='afternoon')
                for practitioner in schedule_dates['Saturday']['morning']:
                    assigned_encounters['Saturday']['morning'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=saturday, session='morning')
                for practitioner in schedule_dates['Saturday']['afternoon']:
                    assigned_encounters['Saturday']['afternoon'][practitioner.practitioner_identifier.identifier] = AssignedEncounter.objects.filter(
                        practitioner_identifier=practitioner.practitioner_identifier.identifier, encounter_date=saturday, session='afternoon')
                encounters = EncounterModel.objects.filter(
                    encounter_status="queued", encounter_location=request.GET['department_schedule'])
            except:
                messages.error(request, "Không tồn tại khoa này")
                return HttpResponseRedirect('/fhir/manage_schedule/')
        encounters = EncounterModel.objects.filter(encounter_status='queued')
        days_of_week = {'Monday': {'date': monday, 'is_future': monday >= now}, 'Tuesday': {'date': tuesday, 'is_future': tuesday >= now}, 'Wednesday': {'date': wednesday, 'is_future': wednesday >=
                                                                                                                                                         now}, 'Thursday': {'date': thursday, 'is_future': thursday >= now}, 'Friday': {'date': friday, 'is_future': friday >= now}, 'Saturday': {'date': saturday, 'is_future': saturday >= now}}

        context = {
            'schedule_dates': schedule_dates,
            'days_of_week': days_of_week,
            'encounters': encounters,
            'assigned_encounters': assigned_encounters,
            'departments': departments
        }
        return render(request, 'fhir/manage_schedule.html', context)

    def post(self, request):
        practitioner = PractitionerModel.objects.get(
            identifier=request.POST['practitioner'])
        encounter = EncounterModel.objects.get(
            encounter_identifier=request.POST['encounter'])
        assigned_encounter = AssignedEncounter.objects.create(practitioner_name=practitioner.name, practitioner_identifier=practitioner,
                                                              assigned_encounter=encounter, encounter_date=request.POST['schedule_date'], session=request.POST['session'])
        encounter.encounter_status = 'assigned'
        encounter.encounter_participant = practitioner.name
        encounter.encounter_participant_identifier = practitioner
        encounter.save()
        return HttpResponseRedirect(self.request.path_info)


class manage_tests(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "medical laboratory technician":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        draft_services = ServiceRequestModel.objects.filter(
            service_category="Laboratory procedure", service_status='draft', service_occurrence=timezone.localtime(timezone.now()).date())
        in_progress_services = ServiceRequestModel.objects.filter(
            service_category="Laboratory procedure", service_status='active', service_occurrence=timezone.localtime(timezone.now()).date())
        completed_services = ServiceRequestModel.objects.filter(
            service_category="Laboratory procedure", service_status='completed', service_occurrence=timezone.localtime(timezone.now()).date())
        context = {
            'draft_services': draft_services,
            'in_progress_services': in_progress_services,
            'completed_services': completed_services
        }
        return render(request, 'fhir/manage_tests.html', context)
        pass

    def post(self, request):
        if request.POST['submit_type'] == 'forward':
            if request.POST['service_type'] == 'draft':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['draft_service_identifier'])
                service.service_status = 'active'
                service.service_performed_date = timezone.localtime(timezone.now()).date()
                service.save()
            elif request.POST['service_type'] == 'in_progress':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['in_progress_service_identifier'])
                service.service_status = 'completed'
                service.save()
        elif request.POST['submit_type'] == 'reverse':
            if request.POST['service_type'] == 'completed':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['completed_service_identifier'])
                service.service_status = 'active'
                service.save()
            elif request.POST['service_type'] == 'in_progress':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['in_progress_service_identifier'])
                service.service_status = 'draft'
                service.service_performed_date = None
                service.service_performer = None
                observations = ObservationModel.objects.filter(
                    service_identifier=service)
                observations.delete()
                service.save()
        return HttpResponseRedirect(self.request.path_info)


class manage_images(LoginRequiredMixin, View):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "diagnostic imaging technician":
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')

        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        draft_services = ServiceRequestModel.objects.filter(
            service_category="Imaging", service_status='draft', service_occurrence=timezone.localtime(timezone.now()).date())
        in_progress_services = ServiceRequestModel.objects.filter(
            service_category="Imaging", service_status='active', service_occurrence=timezone.localtime(timezone.now()).date())
        completed_services = ServiceRequestModel.objects.filter(
            service_category="Imaging", service_status='completed', service_occurrence=timezone.localtime(timezone.now()).date())
        context = {
            'draft_services': draft_services,
            'in_progress_services': in_progress_services,
            'completed_services': completed_services
        }
        return render(request, 'fhir/manage_images.html', context)
        

    def post(self, request):
        if request.POST['submit_type'] == 'forward':
            if request.POST['service_type'] == 'draft':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['draft_service_identifier'])
                service.service_status = 'active'
                service.service_performed_date = timezone.localtime(timezone.now()).date()
                service.save()
            elif request.POST['service_type'] == 'in_progress':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['in_progress_service_identifier'])
                service.service_status = 'completed'
                service.save()
        elif request.POST['submit_type'] == 'reverse':
            if request.POST['service_type'] == 'completed':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['completed_service_identifier'])
                service.service_status = 'active'
                service.save()
            elif request.POST['service_type'] == 'in_progress':
                service = ServiceRequestModel.objects.get(
                    service_identifier=request.POST['in_progress_service_identifier'])
                service.service_status = 'draft'
                service.service_performed_date = None
                service.service_performer = None
                procedure = ProcedureModel.objects.get(
                    service_identifier=service)
                procedure.procedure_status = 'preparation'
                service.save()
        return HttpResponseRedirect(self.request.path_info)
