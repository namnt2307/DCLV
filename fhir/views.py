from django.db.models import query
from django.shortcuts import render, redirect
from django.http import HttpResponse, request, HttpResponseRedirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
import xml.etree.ElementTree as ET
import requests
import uuid
from lib import dttype as dt
from login.forms import UserCreationForm
from handlers import handlers
from fhir.forms import EHRCreationForm
from .models import EncounterModel, MedicationModel, ServiceRequestModel, UserModel, ConditionModel, ObservationModel, ProcedureModel, DiagnosticReportModel, AllergyModel
from .forms import EncounterForm, ConditionForm, ObservationForm, ProcedureForm, ProcedureDetailForm, MedicationForm, RequestForProcedureForm, ServiceRequestForm, RequestForImageForm, DiagnosticReportForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.template.defaulttags import register
import time
# Create your views here.

fhir_server = "http://10.0.0.16:8080/fhir"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


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
    'AMB': 'Ambulatory',
    'FLD': 'Khám tại địa điểm ngoài',
    'EMER': 'Khẩn cấp',
    'HH': 'Khám tại nhà',
    'ACUTE': 'Nội trú khẩn cấp',
    'NONAC': 'Nội trú không khẩn cấp',
    'OBSENC': 'Thăm khám quan sát',
    'SS': 'Ngoại trú',
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
PROCEDURE_CATEGORY_CHOICES = {
    '22642003': 'Phương pháp hoặc dịch vụ tâm thần',
    '409063005': 'Tư vấn',
    '409073007': 'Giáo dục',
    '387713003': 'Phẫu thuật',
    '103693007': 'Chuẩn đoán',
    '46947000': 'Phương pháp chỉnh hình',
    '410606002': 'Phương pháp dịch vụ xã hội'
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
    i = 1
    if request_observations:
        for key, value in request_observations.items():
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_instance, observation_identifier=service_identifier +
                                            '_' + str(i), observation_code=key, observation_category='laboratory', observation_value_unit=value['unit'], observation_reference_range=value['ref_range'])
            i += 1
    else:
        print('no valid data')


@login_required(login_url='/login/')
def user_app(request, group_name, user_name):
    User = get_user_model()
    group_name = User.objects.get(username=user_name).group_name
    page = 'fhir/' + str(group_name) + '.html'
    return render(request, page, {'group_name': group_name, 'user_name': user_name})


@login_required(login_url='/login/')
def patient_view(request, group_name, user_name):
    User = get_user_model()
    patient = {}
    user = User.objects.get(username=user_name)
    user_id = user.identifier
    if user:
        patient['name'] = user.name
        patient['gender'] = user.gender
        patient['birthdate'] = user.birthdate
        patient['address'] = [{'address': user.home_address, 'use': 'home'},
                              {'address': user.work_address, 'use': 'work'}]
        patient['identifier'] = user.identifier
        message = 'Đây là hồ sơ của bạn'
    else:
        message = 'Bạn chưa có hồ sơ khám bệnh'
    return render(request, 'fhir/patient/display.html', {'group_name': group_name, 'user_name': user_name, 'id': user_id, 'patient': patient, 'message': message})


@login_required(login_url='/login/')
def display_detail(request, group_name, user_name, patient_identifier):
    patient = get_user_model()
    encounter_form = EncounterForm()
    data = {'Patient': {}, 'Encounter': []}
    instance = patient.objects.get(
        identifier=patient_identifier)
    data['Patient']['identifier'] = instance.identifier
    data['Patient']['name'] = instance.name
    data['Patient']['birthdate'] = instance.birthdate
    data['Patient']['gender'] = instance.gender
    data['Patient']['home_address'] = instance.home_address
    data['Patient']['work_address'] = instance.work_address
    data['Patient']['telecom'] = instance.telecom
    data['Encounter'] = EncounterModel.objects.all().filter(
        user_identifier=patient_identifier)
    if data['Encounter']:
        data['encounter_type'] = 'list'
    img_dir = f'/static/img/patient/{patient_identifier}.jpg'
    # pass
    return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'img_dir': img_dir, 'form': encounter_form, 'class': ENCOUNTER_CLASS_CHOICES})


class register(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name):
        EHRform = EHRCreationForm()
        User = get_user_model()

        return render(request, 'fhir/doctor/create.html', {'group_name': group_name, 'user_name': user_name, 'form': EHRCreationForm})

    def post(self, request, group_name, user_name):
        User = get_user_model()
        encounter_form = EncounterForm()
        if request.POST:
            data = {'Patient': {}}
            data['Patient']['name'] = request.POST['name']
            data['Patient']['gender'] = request.POST['gender']
            data['Patient']['birthdate'] = request.POST['birthdate']
            data['Patient']['home_address'] = request.POST['home_address']
            data['Patient']['work_address'] = request.POST['work_address']
            data['Patient']['identifier'] = request.POST['identifier']
            data['Patient']['telecom'] = request.POST['telecom']
            # xml_data, data = handlers.register_ehr(patient, id_system)
            get_patient = requests.get(fhir_server + "/Patient?identifier=urn:trinhcongminh|" +
                                       data['Patient']['identifier'], headers={'Content-type': 'application/xml'})
            if get_patient.status_code == 200 and 'entry' in get_patient.content.decode('utf-8'):
                print(get_patient.content.decode('utf-8'))
                data['Patient']['id'] = dt.query_patient(
                    data['Patient']['identifier'])['id']
            patient = dt.create_patient_resource(data['Patient'])
            print(patient)
            if data['Patient'].get('id'):
                print(fhir_server + "/Patient/" +
                      data['Patient']['id'])
                put_patient = requests.put(fhir_server + "/Patient/" + data['Patient']['id'], headers={
                                           'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                print(put_patient.status_code)
                if put_patient.status_code == 200:
                    instance = User.objects.get(
                        identifier=data['Patient']['identifier'])
                    instance.name = data['Patient']['name']
                    instance.gender = data['Patient']['gender']
                    instance.birthdate = data['Patient']['birthdate']
                    instance.home_address = data['Patient']['home_address']
                    instance.work_addresss = data['Patient']['work_address']
                    instance.telecom = data['Patient']['telecom']
                    instance.save()
                    print("save success")
                    return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data})
                else:
                    return HttpResponse("Something wrong when trying to register patient")
            else:
                print('create new resource')
                post_req = requests.post(fhir_server + "/Patient/", headers={
                    'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                print(post_req.status_code)
                if post_req.status_code == 201:
                    print(post_req.content)
                    try:
                        instance = User.objects.get(
                            identifier=data['Patient']['identifier'])
                    except User.DoesNotExist:
                        form = EHRCreationForm(request.POST or None)
                        if form.is_valid():
                            user_n = form.save(commit=False)
                            user_n.username = data['Patient']['identifier']
                            user_n.set_password('nam12345')
                            user_n.group_name = 'patient'
                            user_n.save()
                            form.save()
                        return redirect('/user/'+group_name+'/'+user_name+'/' + 'display-detail' + '/' + data['Patient']['identifier'])
                        # return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'form': encounter_form})
                    else:
                        return HttpResponse("Something wrong when trying to register patient")
        else:
            return HttpResponse("Please enter your information")


class upload(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name):
        return render(request, 'fhir/doctor/upload.html', {'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name):
        if request.FILES.get('excel_file'):
            excel_file = request.FILES.get('excel_file')
            data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
            data = dt.get_patient_upload_data(excel_file)
            patient = dt.create_patient_resource(data['Patient'])
            put_req = None
            post_req = None
            encounter_id = None
            data['Patient']['id'] = dt.query_patient(
                data['Patient']['identifier'])['id']
            if data['Patient']['id']:
                patient = dt.create_patient_resource(data['Patient'])
                put_req = requests.put(fhir_server + "/Patient/"+data['Patient']['id'], headers={
                                       'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
            else:
                post_req = requests.post(fhir_server + "/Patient/", headers={
                                         'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                if post_req.status_code == 201:
                    print(post_req.content)
                    get_root = ET.fromstring(post_req.content.decode('utf-8'))
                    id_resource = get_root.find('d:id', ns)
                    patient_id = id_resource.attrib['value']
            if (put_req and put_req.status_code == 200) or (post_req and post_req.status_code == 201):
                encounter = dt.create_encounter_resource(
                    data['Encounter'], patient_id, data['Patient']['name'])
                post_req = requests.post(fhir_server + "/Encounter/", headers={
                                         'Content-type': 'application/xml'}, data=encounter.decode('utf-8'))
                if post_req.status_code == 201:
                    get_root = ET.fromstring(post_req.content.decode('utf-8'))
                    id_resource = get_root.find('d:id', ns)
                    encounter_id = id_resource.attrib['value']
                    data['Encounter']['id'] = encounter_id
                if data['Observation']:
                    for i in range(len(data['Observation'])):
                        observation = dt.create_observation_resource(
                            data['Observation'][i], data['Patient']['name'], patient_id, encounter_id)
                        post_req = requests.post(fhir_server + "/Observation/", headers={
                                                 'Content-type': 'application/xml'}, data=observation.decode('utf-8'))
                        print(post_req.status_code)
                        print(post_req.content)
                data['encounter_type'] = 'dict'
                if data['Encounter']['period']['start']:
                    data['Encounter']['period']['start'] = dt.getdatetime(
                        data['Encounter']['period']['start'])
                if data['Encounter']['period']['end']:
                    data['Encounter']['period']['end'] = dt.getdatetime(
                        data['Encounter']['period']['end'])
                return render(request, 'fhir/doctor/display.html', {'message': 'Upload successful', 'data': data, 'group_name': group_name, 'user_name': user_name})
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Failed to create resource, please check your file!', 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Please upload your file!', 'group_name': group_name, 'user_name': user_name})


class search(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name):
        return render(request, 'fhir/doctor/search.html', {'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name):
        data = {'Patient': {}, 'Encounter': []}
        patient = get_user_model()
        encounter_form = EncounterForm()
        if request.POST:
            try:
                instance = patient.objects.get(
                    identifier=request.POST['identifier'])
                data['Patient']['identifier'] = instance.identifier
                data['Patient']['name'] = instance.name
                data['Patient']['birthdate'] = datetime.strftime(
                    instance.birthdate, "%d-%m-%Y")
                data['Patient']['gender'] = instance.gender
                data['Patient']['home_address'] = instance.home_address
                data['Patient']['work_address'] = instance.work_address
                data['Patient']['telecom'] = instance.telecom
                data['Encounter'] = EncounterModel.objects.all().filter(
                    user_identifier=instance.identifier)
                get_encounter = requests.get(fhir_server + "/Encounter?subject.identifier=urn:trinhcongminh|" +
                                             request.POST['identifier'], headers={'Content-type': 'application/xml'})
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
                        try:
                            encounter_instance = EncounterModel.objects.get(
                                encounter_identifier=encounter_identifier)
                            if encounter_instance.encounter_storage == 'hapi':
                                encounter_instance.delete()
                                EncounterModel.objects.create(
                                    **encounter, user_identifier=instance, encounter_storage='hapi')
                        except:
                            EncounterModel.objects.create(
                                **encounter, user_identifier=instance, encounter_storage='hapi')
            except patient.DoesNotExist:
                data['Patient'] = dt.query_patient(
                    request.POST['identifier'], query_type='data')
                if data['Patient']:
                    new_patient = patient.objects.create_user(
                        **data['Patient'], username=data['Patient']['identifier'], email='123@gmail.com', password='123')
                    get_encounter = requests.get(fhir_server + "/Encounter?subject.identifier=urn:trinhcongminh|" +
                                                 request.POST['identifier'], headers={'Content-type': 'application/xml'})
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
                            encounter = dt.query_encounter(identifier.find(
                                'd:value', ns).attrib['value'], query_type='data')
                            EncounterModel.objects.create(
                                **encounter, user_identifier=new_patient, encounter_storage='hapi')
                            data['Encounter'].append(encounter)
                else:
                    return HttpResponse('No data found')

            if data:
                data['encounter_type'] = 'list'
                # for encounter in data['Encounter']:
                #     encounter['encounter_class'] = CLASS_CHOICES[encounter['encounter_class']]
                #     encounter['encounter_type'] = TYPE_CHOICES[encounter['encounter_type']]
                patient_identifier = data['Patient']['identifier']
                # return HttpResponseRedirect(f'/user/{group_name}/{user_name}/search/{patient_identifier}')
                return render(request, 'fhir/doctor/search.html', {'message': 'Da tim thay', 'data': data, 'group_name': group_name, 'user_name': user_name, 'form': encounter_form})
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database', 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Please enter an identifier', 'group_name': group_name, 'user_name': user_name})


class hanhchinh(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = patient.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.identifier
        data['Patient']['name'] = instance.name
        data['Patient']['birthdate'] = instance.birthdate
        data['Patient']['gender'] = instance.gender
        data['Patient']['home_address'] = instance.home_address
        data['Patient']['work_address'] = instance.work_address
        # except patient.DoesNotExist:
        #     data['Patient'] = dt.query_patient(patient_identifier)
        #     data['Encounter'] = dt.get_encounter(encounter_identifier)
        #     if data['Encounter']:
        #         data['Observation'] = dt.get_observation(encounter_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Encounter']['identifier'] = encounter_identifier
        if encounter_instance.encounter_storage == 'hapi':
            # get_condition = requests.get(fhir_server + "/Condition?encounter.identifier=urn:trinhcongminh|" +
            #                                 encounter_identifier, headers={'Content-type': 'application/xml'})
            # if get_condition.status_code == 200 and 'entry' in get_condition.content.decode('utf-8'):
            #     get_root = ET.fromstring(
            #         get_condition.content.decode('utf-8'))
            #     data['Condition'] = []
            #     for entry in get_root.findall('d:entry', ns):
            #         condition = {}
            #         resource = entry.find('d:resource', ns)
            #         condition_resource = resource.find('d:Condition', ns)
            #         condition_identifier = condition_resource.find(
            #             'd:identifier', ns)
            #         condition = dt.query_condition(condition_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #         try:
            #             ConditionModel.objects.create(
            #                 **condition, encounter_identifier=encounter_instance)
            #         except Exception as e:
            #             print(e)
            # get_services = requests.get(fhir_server + "/ServiceRequest?encounter.identifier=urn:trinhcongminh|" +
            #                             encounter_identifier, headers={'Content-type': 'application/xml'})
            # if get_services.status_code == 200 and 'entry' in get_services.content.decode('utf-8'):
            #     get_root = ET.fromstring(
            #         get_services.content.decode('utf-8'))
            #     data['Service'] = []
            #     for entry in get_root.findall('d:entry', ns):
            #         service = {}
            #         resource = entry.find('d:resource', ns)
            #         service_resource = resource.find(
            #             'd:ServiceRequest', ns)
            #         service_identifier = service_resource.find(
            #             'd:identifier', ns)
            #         service = dt.query_service(service_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #         ServiceRequestModel.objects.create(
            #             **service, encounter_identifier=encounter_instance)
            #         service_instance = ServiceRequestModel.objects.get(service_identifier=service['service_identifier'])
            #         service_observations = requests.get(fhir_server + "/Observation?based-on.identifier=urn:trinhcongminh|" +
            #                                             service['service_identifier'], headers={'Content-type': 'application/xml'})
            #         if service_observations.status_code == 200 and 'entry' in service_observations.content.decode('utf-8'):
            #             get_root = ET.fromstring(
            #                 service_observations.content.decode('utf-8'))
            #             for entry in get_root.findall('d:entry', ns):
            #                 observation = {}
            #                 resource = entry.find('d:resource', ns)
            #                 observation_resource = resource.find(
            #                     'd:Observation', ns)
            #                 observation_identifier = observation_resource.find(
            #                     'd:identifier', ns)
            #                 observation = dt.query_observation(observation_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #                 observation['service_identifier'] = service_instance
            #                 ObservationModel.objects.create(
            #                     **observation, encounter_identifier=encounter_instance)
            #         get_procedures = requests.get(fhir_server + "/Procedure?based-on.identifier=urn:trinhcongminh|" +
            #                                         service['service_identifier'], headers={'Content-type': 'application/xml'})
            #         if get_procedures.status_code == 200 and 'entry' in get_procedures.content.decode('utf-8'):
            #             get_root = ET.fromstring(
            #                 get_procedures.content.decode('utf-8'))
            #             data['Procedure'] = []
            #             for entry in get_root.findall('d:entry', ns):
            #                 procedure = {}
            #                 resource = entry.find('d:resource', ns)
            #                 procedure_resource = resource.find(
            #                     'd:Procedure', ns)
            #                 procedure_identifier = procedure_resource.find(
            #                     'd:identifier', ns)
            #                 procedure = dt.query_procedure(procedure_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #                 procedure['service_identifier'] = service_instance
            #                 ProcedureModel.objects.create(
            #                     **procedure, encounter_identifier=encounter_instance)
            #         get_diagnostic_reports = requests.get(fhir_server + '/DiagnosticReport?based-on.identifier=urn:trinhcongminh|' + service['service_identifier'], headers={'Content-type': 'application/xml'})
            #         if get_diagnostic_reports.status_code == 200 and 'entry' in get_diagnostic_reports.content.decode('utf-8'):
            #             get_root = ET.fromstring(get_diagnostic_reports.content.decode('utf-8'))
            #             for entry in get_root.findall('d:entry', ns):
            #                 diagnostic_report = {}
            #                 resource = entry.find('d:resource', ns)
            #                 diagnostic_report_resource = resource.find('d:DiagnosticReport' ,ns)
            #                 identifier = diagnostic_report_resource.find('d:identifier', ns)
            #                 diagnostic_report = dt.query_diagnostic_report(identifier.find('d:value', ns).attrib['value'], get_id=False)
            #                 diagnostic_report['service_identifier'] = service_instance
            #                 DiagnosticReportModel.objects.create(**diagnostic_report, encounter_identifier=encounter_instance)
            # get_observations = requests.get(fhir_server + "/Observation?encounter.identifier=urn:trinhcongminh|" +
            #                                 encounter_identifier + "&category:text=vital-signs", headers={'Content-type': 'application/xml'})
            # if get_observations.status_code == 200 and 'entry' in get_observations.content.decode('utf-8'):
            #     get_root = ET.fromstring(
            #         get_observations.content.decode('utf-8'))
            #     for entry in get_root.findall('d:entry', ns):
            #         observation = {}
            #         resource = entry.find('d:resource', ns)
            #         observation_resource = resource.find(
            #             'd:Observation', ns)
            #         observation_identifier = observation_resource.find(
            #             'd:identifier', ns)
            #         observation = dt.query_observation(observation_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #         ObservationModel.objects.create(
            #             **observation, encounter_identifier=encounter_instance)
            # get_medication_statements = requests.get(fhir_server + "/MedicationStatement?context.identifier=urn:trinhcongminh|" +
            #                                             encounter_identifier, headers={'Content-type': 'application/xml'})
            # if get_medication_statements.status_code == 200 and 'entry' in get_medication_statements.content.decode('utf-8'):
            #     get_root = ET.fromstring(
            #         get_medication_statements.content.decode('utf-8'))
            #     data['Medication'] = []
            #     for entry in get_root.findall('d:entry', ns):
            #         medication_statement = {}
            #         resource = entry.find('d:resource', ns)
            #         medication_resource = resource.find(
            #             'd:MedicationStatement', ns)
            #         medication_identifier = medication_resource.find(
            #             'd:identifier', ns)
            #         medication_statement = dt.query_medication(medication_identifier.find('d:value', ns).attrib['value'], get_id=False)
            #         MedicationModel.objects.create(
            #             **medication_statement, encounter_identifier=encounter_instance)
            pass
        elif encounter_instance.encounter_storage == 'local':
            pass
        if data:
            return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        # else:
            # return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = patient.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.identifier
        data['Patient']['name'] = instance.name
        data['Patient']['birthdate'] = instance.birthdate
        data['Patient']['gender'] = instance.gender
        data['Patient']['home_address'] = instance.home_address
        data['Patient']['work_address'] = instance.work_address
        encounter_instances = EncounterModel.objects.all().filter(user_identifier=instance)
        newencounter_identifier = patient_identifier + \
            '_' + str(len(encounter_instances)+1)
        newencounter = EncounterModel.objects.create(
            user_identifier=instance, encounter_identifier=newencounter_identifier)
        data['Encounter']['identifier'] = newencounter.encounter_identifier
        return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name, patient_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = patient.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.identifier
        data['Patient']['name'] = instance.name
        data['Patient']['birthdate'] = instance.birthdate
        data['Patient']['gender'] = instance.gender
        data['Patient']['home_address'] = instance.home_address
        data['Patient']['work_address'] = instance.work_address
        encounter_instances = EncounterModel.objects.all().filter(user_identifier=instance)
        newencounter_identifier = patient_identifier + \
            '_' + str(len(encounter_instances)+1)
        form = EncounterForm(request.POST)
        if form.is_valid():
            encounter_n = form.save(commit=False)
            encounter_n.encounter_identifier = newencounter_identifier
            encounter_n.user_identifier = instance
            encounter_n.encounter_submitted = True
            form.save()
        data['Encounter']['identifier'] = newencounter_identifier
        data['Encounter_Info'] = EncounterModel.objects.get(
            encounter_identifier=newencounter_identifier)
        return redirect('/user/'+group_name+'/' + user_name+'/encounter/'+patient_identifier+'/' + newencounter_identifier + '/hanhchinh')
        # return render(request, 'fhir/hanhchinh.html', {'group_name': group_name, 'user_name': user_name, 'data': data})


class dangky(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Encounter_Info': {}}
        encounter_form = EncounterForm()
        data['Encounter_Info'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Patient']['identifier'] = patient_identifier
        data['Encounter']['identifier'] = encounter_identifier
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=data['Encounter_Info'])
        return render(request, 'fhir/dangky.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'form': encounter_form, 'services': services, 'class': ENCOUNTER_CLASS_CHOICES, 'priority': ENCOUNTER_PRIORITY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Encounter_Info': {}}
        data['Patient']['identifier'] = patient_identifier
        patient = get_user_model()
        instance = patient.objects.get(
            identifier=patient_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = EncounterForm(request.POST, instance=encounter_instance)
        if form.is_valid():
            encounter_n = form.save(commit=False)
            # encounter_n.encounter_identifier = encounter_identifier
            # encounter_n.user_identifier = instance
            encounter_n.encounter_submitted = True
            form.save()
        data['Encounter']['identifier'] = encounter_identifier
        data['Encounter_Info'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        return render(request, 'fhir/dangky.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'class': ENCOUNTER_CLASS_CHOICES, 'priority': ENCOUNTER_PRIORITY_CHOICES})


# class hoibenh(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
#         data = {'Patient': {'identifier': patient_identifier},
#                 'Encounter': {'identifier': encounter_identifier}}
#         encounter = EncounterModel.objects.get(
#             encounter_identifier=encounter_identifier)
#         condition_form = ConditionForm()
#         condition = None
#         try:
#             condition = ConditionModel.objects.get(
#                 encounter_identifier=encounter)
#             print(condition.condition_onset)
#         except:
#             print('somethingwrong')
#             pass
#         services = ServiceRequestModel.objects.all().filter(
#             encounter_identifier=encounter_identifier)

#         return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': condition_form, 'condition': condition, 'clinical': CONDITION_CLINICAL_CHOICES, 'severity': CONDITION_SEVERITY_CHOICES})

#     def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
#         data = {'Patient': {'identifier': patient_identifier},
#                 'Encounter': {'identifier': encounter_identifier}}
#         print(request.POST)
#         encounter_instance = EncounterModel.objects.get(
#             encounter_identifier=encounter_identifier)
#         if request.POST.get('condition_identifier'):
#             condition_identifier = request.POST['condition_identifier']
#             condition_instance = ConditionModel.objects.get(
#                 condition_identifier=condition_identifier)
#             condition_instance.condition_code = request.POST['condition_code']
#             condition_instance.condition_clinical_status = request.POST['condition_clinical_status']
#             condition_instance.condition_onset = request.POST['condition_onset']
#             condition_instance.condition_severity = request.POST['condition_severity']
#             condition_instance.save()
#         else:
#             condition_identifier = encounter_identifier + '_' + \
#                 str(len(ConditionModel.objects.all().filter(
#                     encounter_identifier=encounter_instance))+1)
#             form = ConditionForm(request.POST)
#             if form.is_valid():
#                 condition_n = form.save(commit=False)
#                 condition_n.encounter_identifier = encounter_instance
#                 condition_n.condition_identifier = condition_identifier
#                 condition_n.condition_use = 'admission'
#                 form.save()
#         condition = ConditionModel.objects.get(
#             condition_identifier=condition_identifier)
#         condition_form = ConditionForm()
#         return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'condition': condition, 'clinical': CONDITION_CLINICAL_CHOICES, 'severity': CONDITION_SEVERITY_CHOICES, 'form': condition_form})


class hoibenh_(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        admission_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_instance, condition_note='admission condition by patient')
        resolved_conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_identifier, condition_note='resolved condition by patient')
        allergies = AllergyModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        family_histories = None
        condition_form = ConditionForm()
        context = {
            'group_name': group_name,
            'user_name': user_name,
            'data': data,
            'admission_conditions': admission_conditions,
            'resolved_conditions': resolved_conditions,
            'allergies': allergies,
            'family_histories': family_histories,
            'condition_form': condition_form,
            'severity': CONDITION_SEVERITY_CHOICES
        }
        return render(request, 'fhir/hoibenh.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        conditions = ConditionModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        condition_identifier = encounter_identifier + '_' + str(len(conditions) + 1)
        # for condition in admission_conditions:
        #     condition.delete()
        # resolved_conditions = ConditionModel.objects.all().filter(
        #     encounter_identifier=encounter_identifier, condition_note='resolved condition by patient')            
        # for condition in resolved_conditions:
        #     condition.delete()
        # for key in request.POST.keys():
        #     if key == 'benhly':
        #         content = request.POST[key]
        #         admission_conditions = []
        #         admission_conditions = content.splitlines()
        #         for condition in admission_conditions:
        #             condition_instances = ConditionModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             condition_identifier = encounter_identifier + \
        #                 '_' + str(len(condition_instances) + 1)
        #             condition_content = []
        #             condition_content = condition.split('; ')
        #             condition_object = {}
        #             condition_object['condition_identifier'] = condition_identifier
        #             condition_object['condition_code'] = condition_content[0].strip(
        #             )
        #             condition_object['condition_clinical_status'] = condition_content[1].strip(
        #             )
        #             condition_object['condition_onset'] = condition_content[2].strip(
        #             )
        #             condition_object['condition_severity'] = CONDITION_SEVERITY_VALUES.get(
        #                 condition_content[3].strip().capitalize())
        #             condition_object['condition_note'] = 'admission condition by patient'
        #             condition_object['condition_asserter'] = patient_identifier
        #             ConditionModel.objects.create(
        #                 encounter_identifier=encounter_instance, **condition_object)
        #     elif key == 'tiensubanthan':
        #         content = request.POST[key]
        #         resolved_conditions = []
        #         resolved_conditions = content.splitlines()
        #         for condition in resolved_conditions:
        #             condition_instances = ConditionModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             condition_identifier = encounter_identifier + \
        #                 '_' + str(len(condition_instances) + 1)
        #             condition_content = []
        #             condition_content = condition.split('; ')
        #             condition_object = {}
        #             condition_object['condition_identifier'] = condition_identifier
        #             condition_object['condition_code'] = condition_content[0].strip(
        #             )
        #             condition_object['condition_clinical_status'] = 'resolved'
        #             condition_object['condition_onset'] = condition_content[1].strip(
        #             )
        #             condition_object['condition_abatement'] = condition_content[2].strip(
        #             )
        #             condition_object['condition_severity'] = CONDITION_SEVERITY_VALUES.get(
        #                 condition_content[3].strip().capitalize())
        #             condition_object['condition_note'] = 'resolved condition by patient'
        #             condition_object['condition_asserter'] = patient_identifier
        #             ConditionModel.objects.create(
        #                 encounter_identifier=encounter_instance, **condition_object)
        #     elif key == 'diung':
        #         content = request.POST[key]
        #         allergies = []
        #         allergies = content.splitlines()
        #         for allergy in allergies:
        #             allergy_content = []
        #     elif key == 'tiensugiadinh':
        #         content = request.POST[key]
        #         family_histories = []
        #         family_histories = content.splitlines()
        #         for history in family_histories:
        #             pass
        if request.POST['classifier'] == 'benhly'or request.POST['classifier'] == 'tiensubanthan':
            if request.POST.get('condition_identifier'):
                condition_instance = ConditionModel.objects.get(encounter_identifier=encounter_instance, condition_identifier=request.POST['condition_identifier'])
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
                condition_instance.condition_asserter = patient_identifier
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
                condition_object['condition_asserter'] = patient_identifier
                ConditionModel.objects.create(
                    encounter_identifier=encounter_instance, **condition_object)
        elif request.POST['classifier'] == 'diung':
            pass
        elif request.POST['classifier'] == 'tiensugiadinh':
            pass
        return HttpResponseRedirect(self.request.path_info)


class khambenh(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        observation_instances = ObservationModel.objects.filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')
        observation_objects = {}
        condition_form = ConditionForm()
        print(observation_instances)
        for instance in observation_instances:
            if instance.observation_code.lower() == 'mạch':
                observation_objects['mach'] = instance
            elif instance.observation_code.lower() == 'nhịp thở':
                observation_objects['nhiptho'] = instance
            elif instance.observation_code.lower() == 'huyết áp tâm thu':
                observation_objects['tamthu'] = instance
            elif instance.observation_code.lower() == 'huyết áp tâm trương':
                print('tamtruong')
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
            'group_name': group_name,
            'user_name': user_name,
            'observations': observation_objects,
            'conditions': condition_objects,
            'condition_form': condition_form,
            'severity': CONDITION_SEVERITY_CHOICES
        }
        return render(request, 'fhir/toanthan.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        # for key in request.POST.keys():
        #     print(request.POST.keys())
        #     if request.POST[key]:
        #         if key == 'mach':
        #             observation_instances = ObservationModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             observation_identifier = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 1)
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
        #                                             observation_code='mạch', observation_category='vital-signs', observation_value_quantity=request.POST[key], observation_value_unit='lần/ph')
        #         elif key == 'nhietdo':
        #             observation_instances = ObservationModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             observation_identifier = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 1)
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
        #                                             observation_code='nhiệt độ', observation_category='vital-signs', observation_value_quantity=request.POST[key], observation_value_unit='Cel')
        #         elif key == 'nhiptho':
        #             observation_instances = ObservationModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             observation_identifier = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 1)
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
        #                                             observation_code='nhịp thở', observation_category='vital-signs', observation_value_quantity=request.POST[key], observation_value_unit='lần/ph')
        #         elif key == 'cannang':
        #             observation_instances = ObservationModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             observation_identifier = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 1)
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
        #                                             observation_code='cân nặng', observation_category='vital-signs', observation_value_quantity=request.POST[key], observation_value_unit='kg')
        #         elif key == 'huyetap':
        #             observation_instances = ObservationModel.objects.filter(
        #                 encounter_identifier=encounter_instance)
        #             observation_identifier_1 = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 1)
        #             observation_identifier_2 = encounter_identifier + \
        #                 '_' + str(len(observation_instances) + 2)
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier_1, observation_status='final',
        #                                             observation_code='huyết áp tâm thu', observation_category='vital-signs', observation_value_quantity=request.POST[key].split('/')[0], observation_value_unit='mmHg')
        #             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier_2, observation_status='final',
        #                                             observation_code='huyết áp tâm thu', observation_category='vital-signs', observation_value_quantity=request.POST[key].split('/')[1], observation_value_unit='mmHg')
        #         elif key != 'csrfmiddlewaretoken':
        #             content = request.POST[key]
        #             conditions = []
        #             conditions = content.splitlines()
        #             for condition in conditions:
        #                 condition_instances = ConditionModel.objects.filter(
        #                     encounter_identifier=encounter_instance)
        #                 condition_identifier = encounter_identifier + \
        #                     '_' + str(len(condition_instances) + 1)
        #                 condition_content = condition.split('; ')
        #                 condition_object = {}
        #                 condition_object['condition_identifier'] = condition_identifier
        #                 condition_object['condition_code'] = condition_content[0].strip(
        #                 )
        #                 condition_object['condition_category'] = key
        #                 condition_object['condition_clinical_status'] = 'active'
        #                 condition_object['condition_severity'] = CONDITION_SEVERITY_VALUES.get(
        #                     condition_content[1].strip().capitalize())
        #                 condition_object['condition_note'] = 'admission condition by doctor'
        #                 condition_object['condition_asserter'] = user_name
        #                 ConditionModel.objects.create(
        #                     encounter_identifier=encounter_instance, **condition_object)
        if request.POST['classifier'] == 'observation':
            observation_instances = ObservationModel.objects.filter(
                    encounter_identifier=encounter_instance)            
            count = len(observation_instances)
            if request.POST['mach']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='mạch', observation_category='vital-signs', observation_value_quantity=request.POST['mach'], observation_value_unit='lần/ph')
            if request.POST['nhietdo']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='nhiệt độ', observation_category='vital-signs', observation_value_quantity=request.POST['nhietdo'], observation_value_unit='lần/ph')
            if request.POST['huyetaptamthu']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='huyết áp tâm thu', observation_category='vital-signs', observation_value_quantity=request.POST['huyetaptamthu'], observation_value_unit='lần/ph')
            if request.POST['huyetaptamtruong']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='huyết áp tâm trương', observation_category='vital-signs', observation_value_quantity=request.POST['huyetaptamtruong'], observation_value_unit='lần/ph')
            if request.POST['nhiptho']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='nhịp thở', observation_category='vital-signs', observation_value_quantity=request.POST['nhiptho'], observation_value_unit='lần/ph')                                                                                                                                                                                                
            if request.POST['cannang']:
                count += 1                
                observation_identifier = encounter_identifier + \
                    '_' + str(count)
                ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=observation_identifier, observation_status='final',
                                                observation_code='cân nặng', observation_category='vital-signs', observation_value_quantity=request.POST['cannang'], observation_value_unit='lần/ph')                                                                                                                                                                                                                                                
            pass
        elif request.POST['classifier'] == 'condition':
            if request.POST.get('condition_identifier'):
                condition_instance = ConditionModel.objects.get(encounter_identifier=encounter_instance, condition_identifier=request.POST['condition_identifier'])
                condition_instance.condition_code = request.POST['condition_code']
                condition_instance.condition_clinical_status = 'active'
                condition_instance.condition_severity = request.POST['condition_severity']
                condition_instance.condition_note = 'admission condition by doctor'
                condition_instance.condition_asserter = user_name
                condition_instance.save()
            else:
                conditions = ConditionModel.objects.filter(encounter_identifier=encounter_instance)
                condition_identifier = encounter_identifier + '_' + str(len(conditions) + 1)
                condition_object = {}
                condition_object['condition_identifier'] = condition_identifier
                condition_object['condition_code'] = request.POST['condition_code']
                condition_object['condition_clinical_status'] = 'active'
                condition_object['condition_severity'] = request.POST['condition_severity']
                condition_object['condition_note'] = 'admission condition by doctor'
                condition_object['condition_asserter'] = user_name
                condition_object['condition_category'] = request.POST['condition_category']
                ConditionModel.objects.create(encounter_identifier=encounter_instance, **condition_object)
        return HttpResponseRedirect(self.request.path_info)


class xetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance, service_category='Laboratory procedure')
        service_form = ServiceRequestForm()
        return render(request, 'fhir/xetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': service_form})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = encounter_instance.encounter_identifier + "_" + \
                str(len(ServiceRequestModel.objects.all().filter(
                    encounter_identifier=encounter_instance)) + 1)
            service.service_authored = datetime.now().date()
            service.service_category = 'Laboratory procedure'
            service.service_requester = user_name
            form.save() 
            createobservations(
                encounter_instance, service.service_identifier, service.service_code)
        # services = ServiceRequestModel.objects.all().filter(
        #     encounter_identifier=encounter_instance, service_category='laboratory')
        # service_form = ServiceRequestForm()
        # return render(request, 'fhir/xetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': service_form})
        return HttpResponseRedirect(self.request.path_info)

# class sieuam(View):
#     def get(self, request, group_name, user_name, encounter_id):
#         pass

#     def post(self, request, group_name, user_name, encounter_id):
#         pass


# class service(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request):
#         pass

#     def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
#         data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
#             'identifier': encounter_identifier}, 'Service': {}}
#         encounter_instance = EncounterModel.objects.get(
#             encounter_identifier=encounter_identifier)
#         service_instances = ServiceRequestModel.objects.all().filter(
#             encounter_identifier=encounter_instance)
#         observation_instances = ObservationModel.objects.all().filter(
#             encounter_identifier=encounter_identifier)
#         service_identifier = encounter_identifier + \
#             '_' + str(len(service_instances) + 1)
#         print(service_identifier)
#         service = ServiceRequestModel(encounter_identifier=encounter_instance,
#                                       service_identifier=service_identifier, service_category=request.POST['service_category'])
#         if request.POST['service'] == 'lab1':
#             service.service_location = 'room2'
#             service.service_code = 'Xét nghiệm máu'
#             service.save()
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_1', observation_name='Số lượng bạch cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='cells/mm3')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_2', observation_name='Bạch cầu Lympho', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_3', observation_name='Bạch cầu trung tính', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_4', observation_name='Bạch cầu mono', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_5', observation_name='Bạch cầu ái toan', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_6', observation_name='bạch cầu ái kiềm', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_7', observation_name='Số lượng hồng cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='cells/cm3')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_8', observation_name='Lượng huyết sắc tố trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='g/dl')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_9',
#                                             observation_name='Tỷ lệ thể tích hồng cầu trên thể tích máu toàn phần', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_10', observation_name='Thể tích trung bình của một hồng cầu', observation_category=request.POST['service_category'], observation_value_unit='fl')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_11', observation_name='Lượng huyết sắc tố trung bình trong một hồng cầu', observation_category=request.POST['service_category'], observation_value_unit='pg')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_12',
#                                             observation_name='Nồng độ trung bình của huyết sắc tố hemoglobin trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_13', observation_name='Độ phân bố kích thước hồng cầu', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_14', observation_name='Số lượng tiểu cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='cells/cm3')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_15', observation_name='Độ phân bố kích thước tiểu cầu', observation_category=request.POST['service_category'], observation_value_unit='%')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_16',
#                                             observation_name='Thể tích trung bình của tiểu cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_value_unit='fL')
#         elif request.POST['service'] == 'lab2':
#             service.service_location = 'room3'
#             service.service_code = 'Xét nghiệm nước tiểu'
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_1', observation_name='Leukocytes', observation_category=request.POST['service_category'], observation_value_unit='LEU/UL')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_2', observation_name='Nitrate', observation_category=request.POST['service_category'], observation_value_unit='mg/dL')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_3', observation_name='Urobilinogen', observation_category=request.POST['service_category'], observation_value_unit='mmol/L')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_4', observation_name='Billirubin', observation_category=request.POST['service_category'], observation_value_unit='mmol/L')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_5', observation_name='Protein', observation_category=request.POST['service_category'], observation_value_unit='mg/dL')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_6', observation_name='Chỉ số pH', observation_category=request.POST['service_category'], observation_value_unit='')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_7', observation_name='Blood', observation_category=request.POST['service_category'], observation_value_unit='mg/dL')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_8', observation_name='Specific Gravity', observation_category=request.POST['service_category'], observation_value_unit='Cel')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_9', observation_name='Ketone', observation_category=request.POST['service_category'], observation_value_unit='mg/dL')
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
#                                             '_10', observation_name='Glucose', observation_category=request.POST['service_category'], observation_value_unit='Cel')
#             service.save()
#         elif request.POST['service'] == 'img1':
#             service.service_location = 'room4'
#             service.service_code = 'Chụp X-Quang'
#             service.save()
#         elif request.POST['service'] == 'img2':
#             service.service_location = 'room5'
#             service.service_code = 'Chụp MRI'
#             service.save()
#         elif request.POST['service'] == 'img3':
#             service.service_location = 'room6'
#             service.service_code = 'Siêu âm'
#             service.save()

#         data['Service']['identifier'] = service_identifier
#         services = ServiceRequestModel.objects.all().filter(
#             encounter_identifier=encounter_identifier)
#         observations = ObservationModel.objects.all().filter(
#             service_identifier=service.service_identifier)
#         return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})


# class ketqua(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
#         data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
#             'identifier': encounter_identifier}, 'Service': {'identifier': service_identifier}}
#         services = ServiceRequestModel.objects.all().filter(
#             encounter_identifier=encounter_identifier)
#         observations = ObservationModel.objects.all().filter(
#             service_identifier=service_identifier)
#         return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})

#     def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
#         print(request.POST)
#         observation_list = list(request.POST)
#         print(observation_list)
#         for i in range(1, len(observation_list)):
#             observation = ObservationModel.objects.get(
#                 observation_identifier=observation_list[i])
#             observation.observation_value_quantity = request.POST[observation_list[i]]
#             observation.save()
#         service = ServiceRequestModel.objects.get(
#             service_identifier=service_identifier)
#         service.service_status = 'final'
#         service.save()
#         data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
#             'identifier': encounter_identifier}, 'Service': {'identifier': service_identifier}}
#         services = ServiceRequestModel.objects.all().filter(
#             encounter_identifier=encounter_identifier)
#         observations = ObservationModel.objects.all().filter(
#             service_identifier=service_identifier)
#         return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})


# class toanthan(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
#         data = {'Patient': {'identifier': patient_identifier},
#                 'Encounter': {'identifier': encounter_identifier}}
#         encounter_instance = EncounterModel.objects.get(
#             encounter_identifier=encounter_identifier)
#         observations = ObservationModel.objects.all().filter(
#             encounter_identifier=encounter_instance, observation_category='vital-signs')
#         print(observations)

#         return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name,  'observations': observations})

#     def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
#         data = {'Patient': {'identifier': patient_identifier},
#                 'Encounter': {'identifier': encounter_identifier}}
#         encounter_instance = EncounterModel.objects.get(
#             encounter_identifier=encounter_identifier)
#         count = len(ObservationModel.objects.all().filter(
#             encounter_identifier=encounter_instance))
#         if request.POST['1']:
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Mạch', observation_category='vital-signs', observation_value_quantity=request.POST['1'], observation_value_unit='lần/ph')
#         if request.POST['2']:
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Nhiệt độ', observation_category='vital-signs', observation_value_quantity=request.POST['2'], observation_value_unit='Cel')
#         if request.POST['3']:
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Huyết áp tâm thu', observation_category='vital-signs', observation_value_quantity=request.POST['3'].split('/')[0], observation_value_unit='mmHg')
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Huyết áp tâm trương', observation_category='vital-signs', observation_value_quantity=request.POST['3'].split('/')[1], observation_value_unit='mmHg')
#         if request.POST['4']:
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Nhịp thở', observation_category='vital-signs', observation_value_quantity=request.POST['4'], observation_value_unit='lần/ph')
#         if request.POST['5']:
#             count += 1
#             ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
#                 count), observation_status='final', observation_code='Cân nặng', observation_category='vital-signs', observation_value_quantity=request.POST['5'], observation_value_unit='kg')
#         observations = ObservationModel.objects.all().filter(
#             encounter_identifier=encounter_instance, observation_category='vital-signs')

#         return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'observations': observations})


class thuthuat(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_form = RequestForProcedureForm()
        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        return render(request, 'fhir/thuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'service_form': service_form, 'form': procedure_form, 'procedures': procedures, 'procedure_category': PROCEDURE_CATEGORY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instances = ServiceRequestModel.objects.filter(
            encounter_identifier=encounter_instance)
        service_identifier = encounter_identifier + \
            '_' + str(len(service_instances) + 1)
        form = RequestForProcedureForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = service_identifier
            service.service_authored = datetime.now().date()
            service.service_category = 'laboratory'
            service.service_requester = user_name
            form.save()

        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        return render(request, 'fhir/thuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name,  'form': procedure_form, 'procedures': procedures, 'procedure_category': PROCEDURE_CATEGORY_CHOICES})


class chitietthuthuat(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, procedure_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        form = ProcedureDetailForm()
        procedure = ProcedureModel.objects.get(
            procedure_identifier=procedure_identifier)
        return render(request, 'fhir/chitietthuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'procedure': procedure, 'form': form})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, procedure_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_instance = ProcedureModel.objects.get(
            procedure_identifier=procedure_identifier)
        form = ProcedureDetailForm(request.POST, instance=procedure_instance)
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.procedure_status = 'completed'
            procedure.procedure_performed_datetime = datetime.now()
            form.save()
        return render(request, 'fhir/chitietthuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'procedure': procedure_instance, 'form': form})


class thuoc(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        medications = MedicationModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        medication_form = MedicationForm()
        condition_form = ConditionForm()
        discharge_conditions = ConditionModel.objects.all().filter(encounter_identifier=encounter_instance, condition_note='discharge condition by doctor')
        comorbidity_conditions = ConditionModel.objects.all().filter(encounter_identifier=encounter_instance, condition_note='comorbidity condition by doctor')
        context = {
            'data': data,
            'group_name': group_name,
            'user_name': user_name,
            'medications': medications,
            'discharge_conditions': discharge_conditions,
            'comorbidity_conditions': comorbidity_conditions,
            'medication_form': medication_form,
            'condition_form': condition_form,
            'when': DOSAGE_WHEN_CHOICES,
            'unit': DOSAGE_UNIT_CHOICES,
            'severity': CONDITION_SEVERITY_CHOICES
        }
        return render(request, 'fhir/thuoc.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        print(request.POST)
        if request.POST['classifier'] == 'medication':
            if request.POST.get('medication_identifier'):
                instance = MedicationModel.objects.get(medication_identifier=request.POST['medication_identifier'])
                form = MedicationForm(request.POST or None, instance=instance)
                print(form)
                if form.is_valid():
                    medication = form.save(commit=False)
                    medication.medication_date_asserted = datetime.now().date()
                    form.save()
            else:
                form = MedicationForm(request.POST)
                if form.is_valid():
                    medication = form.save(commit=False)
                    medication.encounter_identifier = encounter_instance
                    medication.medication_identifier = encounter_instance.encounter_identifier + '_' + \
                        str(len(MedicationModel.objects.all().filter(
                            encounter_identifier=encounter_instance)) + 1)
                    medication.medication_date_asserted = datetime.now().date()
                    form.save()
        else:
            if request.POST.get('condition_identifier'):
                instance = ConditionModel.objects.get(condition_identifier=request.POST['condition_identifier'])
                form = ConditionForm(request.POST or None, instance=instance)
                if form.is_valid():
                    condition = form.save(commit=False)
                    condition.condition_clinical_status = 'active'
                    if request.POST['classifier'] == 'discharge':
                        condition.condition_note = 'discharge condition by doctor'
                    else:
                        condition.condition_note = 'comorbidity condition by doctor'
                    condition.condition_asserter = user_name
                    form.save()
            else:
                form = ConditionForm(request.POST)
                if form.is_valid():
                    condition = form.save(commit=False)
                    condition.condition_clinical_status = 'active'
                    condition.condition_identifier = encounter_instance.encounter_identifier + '_' + \
                        str(len(ConditionModel.objects.all().filter(
                            encounter_identifier=encounter_instance)) + 1)
                    condition.encounter_identifier = encounter_instance
                    if request.POST['classifier'] == 'discharge':
                        condition.condition_note = 'discharge condition by doctor'
                    else:
                        condition.condition_note = 'comorbidity condition by doctor'
                    condition.condition_asserter = user_name
                    form.save()
                else:
                    print('form not valid')
        # return render(request, 'fhir/thuoc.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'medications': medications, 'form': medication_form, 'when': DOSAGE_WHEN_CHOICES})
        return HttpResponseRedirect(self.request.path_info)


class chitietxetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        observation_instances = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        return render(request, 'fhir/chitietxetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'service': service_instance, 'observations': observation_instances})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        observation_list = list(request.POST)
        for i in range(1, len(observation_list)):
            observation = ObservationModel.objects.get(
                observation_identifier=observation_list[i])
            observation.observation_value_quantity = request.POST[observation_list[i]]
            observation.observation_performer = user_name
            observation.observation_status = 'final'
            observation.save()
        service_instance.service_status = 'completed'
        service_instance.service_performer = user_name
        service_instance.save()
        # return render(request, 'fhir/chitietxetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'service': service_instance, 'observations': observation_instances})
        return HttpResponseRedirect(self.request.path_info)


class hinhanh(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instances = ServiceRequestModel.objects.filter(
            encounter_identifier=encounter_instance, service_category='Imaging')
        services_data = {}
        service_form = RequestForImageForm()
        procedure_form = ProcedureDetailForm()
        context = {
            'group_name': group_name,
            'user_name': user_name,
            'data': data,
            'service_form': service_form,
            'services': service_instances,
        }
        return render(request, 'fhir/hinhanh.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instances = ServiceRequestModel.objects.filter(
            encounter_identifier=encounter_instance)
        new_service_identifier = encounter_identifier + \
            '_' + str(len(service_instances) + 1)
        service_form = RequestForImageForm()
        form = RequestForImageForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.encounter_identifier = encounter_instance
            service.service_identifier = new_service_identifier
            service.service_authored = datetime.now().date()
            service.service_category = 'Imaging'
            service.service_requester = user_name
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
            new_procedure.procedure_asserter = user_name
            new_procedure.save()
            service_instances = ServiceRequestModel.objects.filter(
                encounter_identifier=encounter_instance, service_category='Imaging')
            context = {
                'group_name': group_name,
                'user_name': user_name,
                'data': data,
                'service_form': service_form,
                'services': service_instances
            }
            return render(request, 'fhir/hinhanh.html', context)
        else:
            return HttpResponse('Form is not valid')


class chitiethinhanh(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        procedure_form = ProcedureDetailForm()
        procedure = ProcedureModel.objects.get(
            encounter_identifier=encounter_instance, service_identifier=service_identifier)
        print(procedure)
        context = {
            'group_name': group_name,
            'user_name': user_name,
            'data': data,
            'procedure_form': procedure_form,
            'procedure': procedure
        }
        return render(request, 'fhir/chitietthuthuat.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        procedure_instance = ProcedureModel.objects.get(
            encounter_identifier=encounter_instance, service_identifier=service_identifier)
        procedure_form = ProcedureForm()
        form = ProcedureDetailForm(request.POST, instance=procedure_instance)
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.procedure_status = 'completed'
            procedure.procedure_performer = user_name
            procedure.procedure_performed_datetime = datetime.now()
            form.save()
            procedure_instance = ProcedureModel.objects.get(
                encounter_identifier=encounter_instance, service_identifier=service_identifier)
            service_instance = ServiceRequestModel.objects.get(
                service_identifier=service_identifier)
            service_instance.performer = user_name
            service_instance.save()
            context = {
                'group_name': group_name,
                'user_name': user_name,
                'data': data,
                'procedure_form': procedure_form,
                'procedure': procedure_instance
            }
            return render(request, 'fhir/chitietthuthuat.html', context)


class chandoan(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        try:
            diagnostic_report_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_instance)
        except:
            diagnostic_report_instance = None
        diagnostic_form = DiagnosticReportForm()
        context = {
            'group_name': group_name,
            'user_name': user_name,
            'data': data,
            'service': service_instance,
            'diagnostic_report': diagnostic_report_instance,
            'diagnostic_form': diagnostic_form
        }
        return render(request, 'fhir/chandoan.html', context)

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        if request.POST.get('diagnostic_identifier'):
            diagnostic_instance = DiagnosticReportModel.objects.get(
                service_identifier=service_identifier)
            diagnostic_instance.diagnostic_conclusion = request.POST['diagnostic_conclusion']
            diagnostic_instance.diagnostic_performer = user_name
            diagnostic_instance.diagnostic_effective = datetime.now()
            diagnostic_instance.save()
        else:
            diagnostic_identifier = encounter_identifier + '_' + \
                str(len(DiagnosticReportModel.objects.all()) + 1)
            form = DiagnosticReportForm(request.POST)
            if form.is_valid():
                diagnostic = form.save(commit=False)
                diagnostic.encounter_identifier = encounter_instance
                diagnostic.service_identifier = service_instance
                diagnostic.diagnostic_identifier = diagnostic_identifier
                diagnostic.diagnostic_effective = datetime.now()
                diagnostic.diagnostic_status = 'registered'
                diagnostic.diagnostic_category = service_instance.service_category
                diagnostic.diagnostic_code = service_instance.service_code
                diagnostic.diagnostic_performer = user_name
                form.save()
        diagnostic_instance = DiagnosticReportModel.objects.get(
            service_identifier=service_identifier)
        diagnostic_form = DiagnosticReportForm()
        context = {
            'group_name': group_name,
            'user_name': user_name,
            'data': data,
            'service': service_instance,
            'diagnostic_report': diagnostic_instance,
            'diagnostic_form': diagnostic_form
        }
        return render(request, 'fhir/chandoan.html', context)


class save(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Condition': []}
        user = get_user_model()
        patient = dt.query_patient(patient_identifier, get_id=True)
        get_encounter = dt.query_encounter(encounter_identifier, query_type='id')
        participant = user.objects.get(username=user_name)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        encounter_instance.encounter_status = 'finished'
        encounter_instance.encounter_end = datetime.now()
        encounter_instance.encounter_participant = user_name
        delta = encounter_instance.encounter_end.date(
        ) - encounter_instance.encounter_start.date()
        if delta.days == 0:
            encounter_instance.encounter_length = '1'
        else:
            encounter_instance.encounter_length = str(delta.days)
        encounter_instance.save()
        practitioner = dt.query_practitioner(
            participant.identifier, query_type='id')
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
        data['Encounter']['priority'] = encounter_instance.encounter_priority
        data['Encounter']['reason_code'] = encounter_instance.encounter_reason
        data['Encounter']['length'] = encounter_instance.encounter_length
        if get_encounter:
            data['Encounter']['id'] = get_encounter['id']
        encounter_data = dt.create_encounter_resource(
            data['Encounter'], patient['id'], patient['name'], practitioner['id'])
        if get_encounter:
            put_encounter = requests.put(fhir_server + "/Encounter/" + get_encounter['id'], headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
            if put_encounter.status_code == 200:
                # print(put_encounter.content.decode('utf-8'))
                encounter_resource = ET.fromstring(put_encounter.content.decode('utf-8'))
                encounter = dt.get_encounter(encounter_resource, query_type='all')
        else:
            post_encounter = requests.post(fhir_server + "/Encounter/", headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
            if post_encounter.status_code == 201:
                encounter_resource = ET.fromstring(post_encounter.content.decode('utf-8'))
                encounter = dt.get_encounter(encounter_resource, query_type='all')                
        encounter_instance.encounter_version = encounter['version']
        encounter_instance.save()
        # encounter = dt.query_encounter(encounter_identifier, query_type='id')
        if encounter:
            condition_instances = ConditionModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            conditions = []
            for condition_instance in condition_instances:
                put_condition = None
                post_condition = None
                condition = {}
                condition['identifier'] = condition_instance.condition_identifier
                condition['clinical_status'] = condition_instance.condition_clinical_status
                condition['verification_status'] = condition_instance.condition_verification_status
                condition['category'] = condition_instance.condition_category
                condition['severity'] = condition_instance.condition_severity
                condition['code'] = condition_instance.condition_code
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
                if get_condition:
                    put_condition = requests.put(fhir_server + "/Condition/"+get_condition['id'], headers={
                        'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
                    if put_condition.status_code == 200:
                        condition_resource = ET.fromstring(put_condition.content.decode('utf-8'))
                        
                        condition_meta = dt.get_condition(condition_resource, query_type='meta')                    
                else:
                    post_condition = requests.post(fhir_server + "/Condition/", headers={
                        'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
                    if post_condition.status_code == 201:
                        condition_resource = ET.fromstring(post_condition.content.decode('utf-8'))
                        
                        condition_meta = dt.get_condition(condition_resource, query_type='meta')                                                           
                condition_instance.condition_version = condition_meta['version']
                condition_instance.save()
            service_instances = ServiceRequestModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for service_instance in service_instances:
                put_service = None
                post_service = None
                service_instance.service_status = 'completed'
                service_instance.save()
                service_requester = user.objects.get(
                    username=service_instance.service_requester)
                requester_identifier = service_requester.identifier
                # print(requester_identifier)
                requester = dt.query_practitioner(
                    requester_identifier, query_type='id')
                service = {}
                service['identifier'] = service_instance.service_identifier
                service['status'] = service_instance.service_status
                service['category'] = service_instance.service_category
                service['intent'] = service_instance.service_intent
                service['requester'] = requester['id']
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
                # print(service_data)
                if get_service:
                    put_service = requests.put(fhir_server + "/ServiceRequest/" + get_service['id'], headers={
                        'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                    # print('put'+ str(put_service.status_code))
                    if put_service.status_code == 200:
                        service_resource = ET.fromstring(put_service.content.decode('utf-8'))
                        
                        service_meta = dt.get_service(service_resource, query_type='all')                                           
                else:
                    post_service = requests.post(fhir_server + "/ServiceRequest/", headers={
                        'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                    # print('post' + str(post_service.status_code))
                    if post_service.status_code == 201:
                        service_resource = ET.fromstring(post_service.content.decode('utf-8'))
                       
                        service_meta = dt.get_service(service_resource, query_type='all')                           
                service_instance.service_version = service_meta['version']
                service_instance.save()
                if (put_service and put_service.status_code == 200) or (post_service and post_service.status_code == 201):
                    service_performer = user.objects.get(
                        username=service_instance.service_performer)
                    performer_identifier = service_performer.identifier
                    performer = dt.query_practitioner(
                        performer_identifier, query_type='id')

                    # service_query = dt.query_service(
                    #     service_instance.service_identifier, query_type='id')
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
                            observation['performer'] = performer['id']
                            get_observation = dt.query_observation(
                                observation['identifier'], query_type='id')
                            if get_observation:
                                observation['id'] = get_observation['id']
                            observation_data = dt.create_observation_resource(
                                observation, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                            if get_observation:
                                put_observation = requests.put(fhir_server + "/Observation/" + get_observation['id'], headers={
                                    'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                                if put_observation.status_code == 200:
                                    observation_resource = ET.fromstring(put_observation.content.decode('utf-8'))
                                    
                                    observation_meta = dt.get_observation(observation_resource, query_type='meta')                                       
                            else:
                                post_observation = requests.post(fhir_server + "/Observation/", headers={
                                    'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                                if post_observation.status_code == 201:
                                    observation_resource = ET.fromstring(post_observation.content.decode('utf-8'))
                                   
                                    observation_meta = dt.get_observation(observation_resource, query_type='meta')                                      
                            observation_instance.observation_version = observation_meta['version']
                            observation_instance.save()
                    if service_instance.proceduremodel_set.all():
                        for procedure_instance in service_instance.proceduremodel_set.all():
                            put_procedure = None
                            post_procedure = None
                            procedure = {}
                            procedure['identifier'] = procedure_instance.procedure_identifier
                            procedure['status'] = procedure_instance.procedure_status
                            procedure['category'] = procedure_instance.procedure_category
                            procedure['code'] = procedure_instance.procedure_code
                            procedure['performed_datetime'] = procedure_instance.procedure_performed_datetime.strftime(
                                '%Y-%m-%dT%H:%M:%S+07:00')
                            procedure['reasonCode'] = procedure_instance.procedure_reason_code
                            procedure['outcome'] = procedure_instance.procedure_outcome
                            procedure['complication'] = procedure_instance.procedure_complication
                            procedure['follow_up'] = procedure_instance.procedure_follow_up
                            procedure['note'] = procedure_instance.procedure_note
                            procedure['used'] = procedure_instance.procedure_used
                            procedure['performer'] = performer['id']
                            procedure['asserter'] = requester['id']
                            get_procedure = dt.query_procedure(
                                procedure['identifier'], query_type='id')
                            print(get_procedure)
                            if get_procedure:
                                procedure['id'] = get_procedure['id']
                            procedure_data = dt.create_procedure_resource(
                                procedure, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                            print(procedure_data)
                            if get_procedure:
                                put_procedure = requests.put(fhir_server + "/Procedure/" + get_procedure['id'], headers={
                                    'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                                # print(put_procedure.content.decode('utf-8'))
                                if put_procedure.status_code == 200:
                                    procedure_resource = ET.fromstring(put_procedure.content.decode('utf-8'))
                                    
                                    procedure_meta = dt.get_procedure(procedure_resource, query_type='meta')                                  
                            else:
                                post_procedure = requests.post(fhir_server + "/Procedure/", headers={
                                    'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                                # print(post_procedure.content.decode('utf-8'))
                                if post_procedure.status_code == 201:
                                    procedure_resource = ET.fromstring(post_procedure.content.decode('utf-8'))
                                
                                    procedure_meta = dt.get_procedure(procedure_resource, query_type='meta')                                   

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
                        diagnostic_report['performer'] = performer['id']
                        get_diagnostic_report = dt.query_diagnostic_report(
                            diagnostic_report['identifier'], query_type='id')
                        if get_diagnostic_report:
                            diagnostic_report['id'] = get_diagnostic_report['id']
                        diagnostic_report_data = dt.create_diagnostic_report_resource(
                            diagnostic_report, patient['id'], patient['name'], encounter['id'], service_meta['id'])
                        if get_diagnostic_report:
                            put_diagnostic_report = requests.put(fhir_server + '/DiagnosticReport/' + diagnostic_report['id'], headers={
                                'Content-type': 'application/xml'}, data=diagnostic_report_data.decode('utf-8'))
                            if put_diagnostic_report.status_code == 200:
                                diagnostic_report_resource = ET.fromstring(put_diagnostic_report.content.decode('utf-8'))
                                
                                diagnostic_report_meta = dt.get_diagnostic_report(diagnostic_report_resource, query_type='meta')                                   
                        else:
                            post_diagnostic_report = requests.post(fhir_server + '/DiagnosticReport/', headers={
                                'Content-type': 'application/xml'}, data=diagnostic_report_data.decode('utf-8'))
                            if post_diagnostic_report.status_code == 201:
                                diagnostic_report_resource = ET.fromstring(post_diagnostic_report.content.decode('utf-8'))
                                
                                diagnostic_report_meta = dt.get_diagnostic_report(diagnostic_report_resource, query_type='meta')                                    

                        diagnostic_report_instance.diagnostic_version = diagnostic_report_meta['version']
                        diagnostic_report_instance.save()
                    except Exception as e:
                        print(e)
                        print('no diagnostic')
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
                get_observation = dt.query_observation(
                    observation['identifier'], query_type='id')
                if get_observation:
                    observation['id'] = get_observation['id']
                observation_data = dt.create_observation_resource(
                    observation, patient['id'], patient['name'], encounter['id'])
                if get_observation:
                    put_observation = requests.put(fhir_server + "/Observation/" + get_observation['id'], headers={
                        'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                    if put_observation.status_code == 200:
                        observation_resource = ET.fromstring(put_observation.content.decode('utf-8'))
                        
                        observation_meta = dt.get_observation(observation_resource, query_type='meta')                          
                else:
                    post_observation = requests.post(fhir_server + "/Observation/", headers={
                        'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                    if post_observation.status_code == 201:
                        observation_resource = ET.fromstring(post_observation.content.decode('utf-8'))
                       
                        observation_meta = dt.get_observation(observation_resource, query_type='meta')                          
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
                medication['frequency'] = medication_instance.dosage_frequency
                medication['period'] = medication_instance.dosage_period + ' ' + medication_instance.dosage_period_unit
                medication['duration'] = medication_instance.dosage_duration + ' ' + medication_instance.dosage_duration_unit
                medication['when'] = medication_instance.dosage_when
                medication['offset'] = medication_instance.dosage_offset
                medication['route'] = medication_instance.dosage_route
                medication['quantity'] = medication_instance.dosage_quantity
                get_medication = dt.query_medication(
                    medication['identifier'], query_type='id')
                print(get_medication)
                if get_medication:
                    medication['id'] = get_medication['id']
                medication_data = dt.create_medication_resource(
                    medication, patient['id'], patient['name'], encounter['id'])
                if get_medication:
                    put_medication = requests.put(fhir_server + "/MedicationStatement/" + get_medication['id'], headers={
                        'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                    # print(put_medication.content.decode('utf-8'))
                    if put_medication.status_code == 200:
                        medication_resource = ET.fromstring(put_medication.content.decode('utf-8'))
                      
                        medication_meta = dt.get_observation(medication_resource, query_type='meta')                          
                else:
                    post_medication = requests.post(fhir_server + "/MedicationStatement/", headers={
                        'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                    if post_medication.status_code == 201:
                        medication_resource = ET.fromstring(post_medication.content.decode('utf-8'))
                       
                        medication_meta = dt.get_observation(medication_resource, query_type='meta')                          
                medication_instance.medication_version = medication_meta['version']
                medication_instance.save()
            return HttpResponse('Success')
        else:
            return HttpResponse('Something Wrong')


class view_benhan(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier},
                'Observation': {}}
        patient = get_user_model().objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        encounter_history = []
        if encounter.encounter_version > 1:
            encounter_id = dt.query_encounter(encounter_identifier, query_type='id')['id']  
            for i in range(encounter.encounter_version-1, 0, -1):
                encounter_history.append(dt.query_encounter_history(encounter_id, str(i), query_type='all'))
        admission_conditions = {'patient': [], 'doctor': {'toanthan': [], 'tuanhoan': [], 'hohap': [
        ], 'tieuhoa': [], 'tts': [], 'thankinh': [], 'cxk': [], 'tmh': [], 'rhm': [], 'mat': [], 'noitiet': []}}
        resolved_conditions = []
        conditions_history = {}
        observations_history = {}
        discharge_conditions = []
        comorbidity_conditions = []
        diagnostic_reports = []
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
            comorbidity_conditions = ConditionModel.objects.filter(
                encounter_identifier=encounter, condition_note='comorbidity condition by doctor')
            conditions = ConditionModel.objects.filter(encounter_identifier=encounter)
            for condition in conditions:
                conditions_history[condition.condition_identifier] = []
                if condition.condition_version > 1:
                    condition_id = dt.query_condition(condition.condition_identifier, query_type='id')['id']  
                    for i in range(condition.condition_version-1, 0, -1):
                        conditions_history[condition.condition_identifier].append(dt.query_condition_history(condition_id, str(i), query_type='all'))
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
                if observation.observation_version != 0 and observation.observation_version > 1:
                    observation_id = dt.query_observation(observation.observation_identifier, query_type='id')['id']  
                    observations_history[observation.observation_identifier] = []
                    for i in range(observation.observation_version-1, 0, -1):
                        observations_history[observation.observation_identifier].append(dt.query_observation_history(observation_id, str(i), query_type='all'))
            diagnostic_reports = DiagnosticReportModel.objects.filter(encounter_identifier=encounter)
        elif encounter.encounter_storage == 'hapi':
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
                    condition = dt.query_condition(condition_identifier.find(
                        'd:value', ns).attrib['value'], query_type='all')
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
                    if int(condition['version']) > 1:
                        conditions_history[condition['condition_identifier']] = []
                        for i in range(int(condition['version'])-1, 0, -1):
                            conditions_history[condition['condition_identifier']].append(dt.query_condition_history(condition['id'], str(i), query_type='all'))
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
                    if int(observation['version']) > 1:
                        observations_history[observation['observation_identifier']] = []
                        for i in range(int(observation['version'])-1, 0 , -1):
                            observations_history[observation['observation_identifier']].append(dt.query_observation_history(observation['id'], str(i), query_type='all'))
        context = {
            'data': data,
            'group_name': group_name,
            'user_name': user_name,
            'patient': patient,
            'encounter': encounter,
            'encounter_history': encounter_history,
            'admission_conditions': admission_conditions,
            'resolved_conditions': resolved_conditions,
            'discharge_conditions': discharge_conditions,
            'comorbidity_conditions': comorbidity_conditions,
            'conditions_history': conditions_history,
            'observations_history': observations_history,
            'diagnostic_reports': diagnostic_reports,
            'severity': CONDITION_SEVERITY_CHOICES
        }
        return render(request, 'fhir/view/benhan.html', context)


class view_xetnghiem(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier},
                'Observation': {}}
        patient = get_user_model().objects.get(identifier=patient_identifier)
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
                    service_id = dt.query_service(service.service_identifier, query_type='id')['id']  
                    for i in range(service.service_version-1, 0, -1):
                        services_history[service.service_identifier].append(dt.query_service_history(service_id, str(i), query_type='all'))
                observations[service.service_identifier] = ObservationModel.objects.filter(encounter_identifier=encounter, service_identifier=service)
                for observation in observations[service.service_identifier]:
                    if observation.observation_version > 1:
                        observations_history[observation.observation_identifier] = []
                        observation_id = dt.query_observation(observation.observation_identifier, query_type='id')['id']  
                        for i in range(observation.observation_version-1, 0, -1):
                            observations_history[observation.observation_identifier].append(dt.query_observation_history(observation_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
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
                    service = dt.query_service(service_identifier.find('d:value', ns).attrib['value'], query_type='all')
                    services.append(service)
                    if int(service['version']) > 1:
                        services_history[service['service_identifier']] = []
                        for i in range(int(service['version'])-1, 0, -1):
                            services_history[service['service_identifier']].append(dt.query_service_history(service['id'], str(i), query_type='all'))
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
                            observation = dt.query_observation(observation_identifier.find('d:value', ns).attrib['value'], query_type='all')                   
                            observations[service['service_identifier']].append(observation)
                            if int(observation['version']) > 1:
                                observations_history[observation['observation_identifier']] = []
                                for i in range(int(observation['version'])-1, 0, -1):
                                    observations_history[observation['observation_identifier']].append(dt.query_observation_history(observation['id'], str(i), query_type='all'))
        context = {
            'data': data,
            'group_name': group_name,
            'user_name': user_name,
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

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        patient = get_user_model().objects.get(identifier=patient_identifier)
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = []
        procedures = {}
        diagnostic_reports = {}
        services_history = {}
        procedures_history = {}
        diagnostic_reports_history = {}
        if encounter.encounter_storage == 'local':
            services = ServiceRequestModel.objects.filter(
                encounter_identifier=encounter, service_category='Imaging')
            for service in services:
                if service.service_version > 1:
                    services_history[service.service_identifier] = []
                    service_id = dt.query_service(service.service_identifier, query_type='id')['id']  
                    for i in range(service.service_version-1, 0 ,-1):
                        services_history[service.service_identifier].append(dt.query_condition_history(service_id, str(i), query_type='all'))
                procedures[service.service_identifier] = ProcedureModel.objects.filter(encounter_identifier=encounter, service_identifier=service)
                for procedure in procedures[service.service_identifier]:
                    if procedure.procedure_version > 1:
                        procedures_history[procedure.procedure_identifier] = []
                        procedure_id = dt.query_procedure(procedure.procedure_identifier, query_type='id')['id']  
                        for i in range(procedure.procedure_version-1, 0 ,-1):
                            procedures_history[procedure.procedure_identifier].append(dt.query_procedure_history(procedure_id, str(i), query_type='all'))
                diagnostic_reports[service.service_identifier] = DiagnosticReportModel.objects.filter(encounter_identifier=encounter, service_identifier=service)
                for diagnostic_report in diagnostic_reports[service.service_identifier]:
                    if diagnostic_report.diagnostic_version > 1:
                        diagnostic_reports_history[diagnostic_report.diagnostic_identifier] = []
                        diagnostic_report_id = dt.query_diagnostic_report(diagnostic_report.diagnostic_identifier, query_type='id')['id']  
                        for i in range(diagnostic_report.diagnostic_version-1, 0, -1):
                            diagnostic_reports_history[diagnostic_report.diagnostic_identifier].append(dt.query_diagnostic_report_history(diagnostic_report_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
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
                    service = dt.query_service(service_identifier.find('d:value', ns).attrib['value'], query_type='all')
                    services.append(service)
                    if int(service['version']) > 1:
                        services_history[service['service_identifier']] = []
                        for i in range(int(service['version'])-1, 0, -1):
                            services_history[service['service_identifier']].append(dt.query_service_history(service['id'], str(i), query_type='all'))
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
                            procedure = dt.query_procedure(procedure_identifier.find('d:value', ns).attrib['value'], query_type='all')
                            procedures[service['service_identifier']].append(procedure)
                            if int(procedure['version']) > 1:
                                procedures_history[procedure['procedure_identifier']] = []
                                for i in range(int(procedure['version'])-1, 0, -1):
                                    procedures_history[procedure['procedure_identifier']].append(dt.query_procedure_history(service['id'], str(i), query_type='all'))
                    diagnostic_reports[service['service_identifier']] = []
                    get_diagnostic_reports = requests.get(fhir_server + '/DiagnosticReport?based-on.identifier=urn:trinhcongminh|' + service['service_identifier'], headers={'Content-type': 'application/xml'})
                    if get_diagnostic_reports.status_code == 200 and 'entry' in get_diagnostic_reports.content.decode('utf-8'):
                        get_root = ET.fromstring(get_diagnostic_reports.content.decode('utf-8'))
                        for entry in get_root.findall('d:entry', ns):
                            diagnostic_report = {}
                            resource = entry.find('d:resource', ns)
                            diagnostic_report_resource = resource.find('d:DiagnosticReport' ,ns)
                            identifier = diagnostic_report_resource.find('d:identifier', ns)
                            diagnostic_report = dt.query_diagnostic_report(identifier.find('d:value', ns).attrib['value'], query_type='all')
                            diagnostic_reports[service['service_identifier']].append(diagnostic_report)
                            if int(diagnostic_report['version']) > 1:
                                diagnostic_reports_history[diagnostic_report['diagnostic_identifier']] = []
                                for i in range(int(diagnostic_report['version'])-1, 0, -1):
                                    diagnostic_reports_history[diagnostic_report['diagnostic_identifier']].append(dt.query_diagnostic_report_history(diagnostic_report['id'], str(i), query_type='all'))
        context = {
            'data': data,
            'group_name': group_name,
            'user_name': user_name,
            'patient': patient,
            'encounter': encounter,
            'services': services,
            'procedures': procedures,
            'diagnostic_reports': diagnostic_reports,
            'services_history': services_history,
            'procedures_history': procedures_history,
            'diagnostic_reports_history': diagnostic_reports_history,
            
        }
        return render(request, 'fhir/view/phieuthuthuat.html', context)


class view_donthuoc(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        patient = get_user_model().objects.get(identifier=patient_identifier)
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
                    medication_id = dt.query_medication(medication.medication_identifier, query_type='id')['id']  
                    for i in range(medication.medication_version-1, 0, -1):
                        medications_history[medication.medication_identifier].append(dt.query_medication_history(medication_id, str(i), query_type='all'))
        elif encounter.encounter_storage == 'hapi':
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
                    medication_statement = dt.query_medication(medication_identifier.find('d:value', ns).attrib['value'], query_type='all')
                    medications.append(medication_statement)          
                    if int(medication_statement['version']) > 1:
                        medications_history[medication_statement['medication_identifier']] = []
                        for i in range(int(medication_statement['version'])-1, 0, -1):
                            medications_history[medication_statement['medication_identifier']].append(dt.query_medication_history(medication_statement['id'], str(i), query_type='all'))
        context = {
            'data': data,
            'group_name': group_name,
            'user_name': user_name,
            'patient': patient,
            'encounter': encounter,
            'medications': medications,
            'medications_history': medications_history,
            'when': DOSAGE_WHEN_CHOICES,
            'unit': DOSAGE_UNIT_CHOICES
        }
        return render(request, 'fhir/view/donthuoc.html', context)
