from django.shortcuts import render
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
from .models import EncounterModel, MedicationModel, ServiceRequestModel, UserModel, ConditionModel, ObservationModel, ProcedureModel
from .forms import EncounterForm, ConditionForm, ObservationForm, ProcedureForm, ProcedureDetailForm, MedicationForm, ServiceRequestForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.template.defaulttags import register
# Create your views here.


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


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

PROCEDURE_CATEGORY_CHOICES = {
    '22642003': 'Phương pháp hoặc dịch vụ tâm thần',
    '409063005': 'Tư vấn',
    '409073007': 'Giáo dục',
    '387713003': 'Phẫu thuật',
    '103693007': 'Chuẩn đoán',
    '46947000': 'Phương pháp chỉnh hình',
    '410606002': 'Phương pháp dịch vụ xã hội'
}

id_system = "urn:trinhcongminh"

ns = {'d': "http://hl7.org/fhir"}


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
        patient['birthDate'] = user.birthDate
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
    data['Patient']['birthDate'] = instance.birthDate
    print(data['Patient']['birthDate'])
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
    return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'img_dir': img_dir, 'form': encounter_form, 'class':ENCOUNTER_CLASS_CHOICES})


class register(LoginRequiredMixin, View):
    login_url='/login/'
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
            data['Patient']['birthDate'] = request.POST['birthDate']
            data['Patient']['home_address'] = request.POST['home_address']
            data['Patient']['work_address'] = request.POST['work_address']
            data['Patient']['identifier'] = request.POST['identifier']
            data['Patient']['telecom'] = request.POST['telecom']
            # xml_data, data = handlers.register_ehr(patient, id_system)
            get_patient = requests.get("http://hapi.fhir.org/baseR4/Patient?identifier=urn:trinhcongminh|" +
                                       data['Patient']['identifier'], headers={'Content-type': 'application/xml'})
            if get_patient.status_code == 200 and 'entry' in get_patient.content.decode('utf-8'):
                data['Patient']['id'] = dt.query_patient(
                    data['Patient']['identifier'])['id']
            patient = dt.create_patient_resource(data['Patient'])
            print(patient)
            if data['Patient'].get('id'):
                print("http://hapi.fhir.org/baseR4/Patient/" +
                      data['Patient']['id'])
                put_patient = requests.put("http://hapi.fhir.org/baseR4/Patient/" + data['Patient']['id'], headers={
                                           'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                print(put_patient.status_code)
                if put_patient.status_code == 200:
                    instance = User.objects.get(
                        identifier=data['Patient']['identifier'])
                    instance.name = data['Patient']['name']
                    instance.gender = data['Patient']['gender']
                    instance.birthDate = data['Patient']['birthDate']
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
                post_req = requests.post("http://hapi.fhir.org/baseR4/Patient/", headers={
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
                        return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'form': encounter_form})
                    else:
                        return HttpResponse("Something wrong when trying to register patient")
        else:
            return HttpResponse("Please enter your information")


class upload(LoginRequiredMixin, View):
    login_url='/login/'
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
                put_req = requests.put("http://hapi.fhir.org/baseR4/Patient/"+data['Patient']['id'], headers={
                                       'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
            else:
                post_req = requests.post("http://hapi.fhir.org/baseR4/Patient/", headers={
                                         'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                if post_req.status_code == 201:
                    print(post_req.content)
                    get_root = ET.fromstring(post_req.content.decode('utf-8'))
                    id_resource = get_root.find('d:id', ns)
                    patient_id = id_resource.attrib['value']
            if (put_req and put_req.status_code == 200) or (post_req and post_req.status_code == 201):
                encounter = dt.create_encounter_resource(
                    data['Encounter'], patient_id, data['Patient']['name'])
                post_req = requests.post("http://hapi.fhir.org/baseR4/Encounter/", headers={
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
                        post_req = requests.post("http://hapi.fhir.org/baseR4/Observation/", headers={
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
    login_url='/login/'
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
                data['Patient']['birthDate'] = datetime.strftime(
                    instance.birthDate, "%d-%m-%Y")
                print(data['Patient']['birthDate'])
                data['Patient']['gender'] = instance.gender
                data['Patient']['home_address'] = instance.home_address
                data['Patient']['work_address'] = instance.work_address
                data['Patient']['telecom'] = instance.telecom
                data['Encounter'] = EncounterModel.objects.all().filter(
                    user_identifier=instance.identifier)
            except patient.DoesNotExist:
                data['Patient'] = dt.query_patient(request.POST['identifier'])
                print(data['Patient'])
                if data['Patient']:
                    print(data['Patient'])
                    create_data = data['Patient']
                    create_data.pop('id', None)
                    new_patient = patient.objects.create_user(
                        **create_data, username=data['Patient']['identifier'], email='123@gmail.com', password='123')
                    get_encounter = requests.get("http://hapi.fhir.org/baseR4/Encounter?subject.identifier=urn:trinhcongminh|" +
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
                            encounter['encounter_identifier'] = identifier.find(
                                'd:value', ns).attrib['value']
                            encounter['encounter_status'] = encounter_resource.find(
                                'd:status', ns).attrib['value']
                            _class = encounter_resource.find('d:class', ns)
                            encounter['encounter_class'] = _class.find(
                                'd:code', ns).attrib['value']
                            _type = encounter_resource.find('d:type', ns)
                            encounter['encounter_type'] = _type.find(
                                'd:text', ns).attrib['value']
                            servicetype = encounter_resource.find(
                                'd:serviceType', ns)
                            encounter['encounter_service'] = servicetype.find(
                                'd:text', ns).attrib['value']
                            priority = encounter_resource.find(
                                'd:priority', ns)
                            priority_coding = priority.find('d:coding', ns)
                            encounter['encounter_priority'] = priority_coding.find(
                                'd:value', ns)
                            period = encounter_resource.find('d:period', ns)
                            encounter['encounter_start'] = dt.getdatetime(
                                period.find('d:start', ns).attrib['value'])
                            end_date = None
                            if period.find('d:end', ns) != None:
                                end_date = period.find(
                                    'd:end', ns).attrib['value']
                                encounter['encounter_end'] = dt.getdatetime(
                                    end_date)
                            reason = encounter_resource.find(
                                'd:reasonCode', ns)
                            encounter['encounter_reason'] = reason.find(
                                'd:text', ns).attrib['value']
                            encounter['encounter_submitted'] = True
                            EncounterModel.objects.create(
                                **encounter, user_identifier=new_patient)
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
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = patient.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.identifier
        data['Patient']['name'] = instance.name
        data['Patient']['birthDate'] = instance.birthDate
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
        if encounter_instance.encounter_status == 'finished':
            conditions = ConditionModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            if len(conditions) == 0:
                get_condition = requests.get("http://hapi.fhir.org/baseR4/Condition?encounter.identifier=urn:trinhcongminh|" +
                                             encounter_identifier, headers={'Content-type': 'application/xml'})
                if get_condition.status_code == 200 and 'entry' in get_condition.content.decode('utf-8'):
                    get_root = ET.fromstring(
                        get_condition.content.decode('utf-8'))
                    data['Condition'] = []
                    for entry in get_root.findall('d:entry', ns):
                        condition = {}
                        resource = entry.find('d:resource', ns)
                        condition_resource = resource.find('d:Condition', ns)
                        print(condition_resource.find(
                            'd:id', ns).attrib['value'])
                        condition_identifier = condition_resource.find(
                            'd:identifier', ns)
                        condition['condition_identifier'] = condition_identifier.find(
                            'd:value', ns).attrib['value']
                        clinicalstatus = condition_resource.find(
                            'd:clinicalStatus', ns)
                        clinicalstatus_coding = clinicalstatus.find(
                            'd:coding', ns)
                        condition['condition_clinicalstatus'] = clinicalstatus_coding.find(
                            'd:code', ns).attrib['value']
                        severity = condition_resource.find('d:severity', ns)
                        condition['condition_severity'] = severity.find(
                            'd:text', ns).attrib['value']
                        code = condition_resource.find('d:code', ns)
                        condition['condition_code'] = code.find(
                            'd:text', ns).attrib['value']
                        onset = condition_resource.find('d:onsetDateTime', ns)
                        condition['condition_onset'] = dt.getdatetime(
                            onset.attrib['value'])
                        ConditionModel.objects.create(
                            **condition, encounter_identifier=encounter_instance)
            services = ServiceRequestModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            print(services)
            if len(services) == 0:
                get_services = requests.get("http://hapi.fhir.org/baseR4/ServiceRequest?encounter.identifier=urn:trinhcongminh|" +
                                            encounter_identifier, headers={'Content-type': 'application/xml'})
                if get_services.status_code == 200 and 'entry' in get_services.content.decode('utf-8'):
                    get_root = ET.fromstring(
                        get_services.content.decode('utf-8'))
                    data['Service'] = []
                    for entry in get_root.findall('d:entry', ns):
                        service = {}
                        resource = entry.find('d:resource', ns)
                        service_resource = resource.find(
                            'd:ServiceRequest', ns)
                        service_identifier = service_resource.find(
                            'd:identifier', ns)
                        service['service_identifier'] = service_identifier.find(
                            'd:value', ns).attrib['value']
                        service['service_status'] = service_resource.find(
                            'd:status', ns).attrib['value']
                        category = service_resource.find('d:category', ns)
                        service['service_category'] = category.find(
                            'd:text', ns).attrib['value']
                        code = service_resource.find('d:code', ns)
                        service['service_code'] = code.find(
                            'd:text', ns).attrib['value']
                        service['service_occurrence'] = service_resource.find('d:occurrenceDateTime', ns).attrib['value']
                        service['service_authored'] = service_resource.find('d:authoredOn', ns).attrib['value']
                        note = service_resource.find('d:note', ns)
                        if note:
                            service['service_note'] = note.find('d:text', ns).attrib['value']
                        ServiceRequestModel.objects.create(
                            **service, encounter_identifier=encounter_instance)
                        service_observations = requests.get("http://hapi.fhir.org/baseR4/Observation?based-on.identifier=urn:trinhcongminh|" +
                                                            service['service_identifier'], headers={'Content-type': 'application/xml'})
                        print(service_observations.content)
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
                                observation['observation_identifier'] = observation_identifier.find(
                                    'd:value', ns).attrib['value']
                                observation['observation_status'] = observation_resource.find(
                                    'd:status', ns).attrib['value']
                                category = observation_resource.find(
                                    'd:category', ns)
                                observation['observation_category'] = category.find(
                                    'd:text', ns).attrib['value']
                                code = observation_resource.find('d:code', ns)
                                observation['observation_code'] = code.find(
                                    'd:text', ns).attrib['value']
                                effective = observation_resource.find(
                                    'd:effectiveDateTime', ns).attrib['value']
                                observation['observation_effective'] = dt.getdatetime(
                                    effective)
                                valuequantity = observation_resource.find(
                                    'd:valueQuantity', ns)
                                observation['observation_valuequantity'] = valuequantity.find(
                                    'd:value', ns).attrib['value']
                                unit = valuequantity.find('d:unit', ns)
                                if unit is not None:
                                    observation['observation_valueunit'] = unit.attrib['value']

                                observation['service_identifier'] = service['service_identifier']
                                ObservationModel.objects.create(
                                    **observation, encounter_identifier=encounter_instance)
                        else:
                            pass
                else:
                    pass
            observations = ObservationModel.objects.all().filter(
                encounter_identifier=encounter_instance, observation_category='vital-signs')
            if len(observations) == 0:
                get_observations = requests.get("http://hapi.fhir.org/baseR4/Observation?encounter.identifier=urn:trinhcongminh|" +
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
                        observation['observation_identifier'] = observation_identifier.find(
                            'd:value', ns).attrib['value']
                        observation['observation_status'] = observation_resource.find(
                            'd:status', ns).attrib['value']
                        category = observation_resource.find('d:category', ns)
                        observation['observation_category'] = category.find(
                            'd:text', ns).attrib['value']
                        code = observation_resource.find('d:code', ns)
                        observation['observation_code'] = code.find(
                            'd:text', ns).attrib['value']
                        effective = observation_resource.find(
                            'd:effectiveDateTime', ns).attrib['value']
                        observation['observation_effective'] = dt.getdatetime(
                            effective)
                        valuequantity = observation_resource.find(
                            'd:valueQuantity', ns)
                        observation['observation_valuequantity'] = valuequantity.find(
                            'd:value', ns).attrib['value']
                        unit = valuequantity.find('d:unit', ns)
                        if unit is not None:
                            observation['observation_valueunit'] = unit.attrib['value']
                            print(observation['observation_valueunit'])
                            # print(unit.attrib['value'])
                        ObservationModel.objects.create(
                            **observation, encounter_identifier=encounter_instance)
                else:
                    pass
            else:
                pass
            procedures = ProcedureModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            if len(procedures) == 0:
                get_procedures = requests.get("http://hapi.fhir.org/baseR4/Procedure?encounter.identifier=urn:trinhcongminh|" +
                                             encounter_identifier, headers={'Content-type': 'application/xml'})
                if get_procedures.status_code == 200 and 'entry' in get_procedures.content.decode('utf-8'):
                    get_root = ET.fromstring(
                        get_procedures.content.decode('utf-8'))
                    data['Procedure'] = []    
                    for entry in get_root.findall('d:entry', ns):
                        procedure = {}
                        resource = entry.find('d:resource', ns)
                        procedure_resource = resource.find(
                            'd:Procedure', ns)
                        procedure_identifier = procedure_resource.find(
                            'd:identifier', ns)
                        procedure['procedure_identifier'] = procedure_identifier.find(
                            'd:value', ns).attrib['value']
                        procedure['procedure_status'] = procedure_resource.find(
                            'd:status', ns).attrib['value']
                        category = procedure_resource.find('d:category', ns)
                        procedure['procedure_category'] = category.find(
                            'd:text', ns).attrib['value']
                        code = procedure_resource.find('d:code', ns)
                        procedure['procedure_code'] = code.find(
                            'd:text', ns).attrib['value']
                        performedDateTime = procedure_resource.find('d:performedDateTime', ns)
                        procedure['procedure_performedDateTime'] = dt.getdatetime(performedDateTime.attrib['value'])
                        reasonCode = procedure_resource.find('d:reasonCode', ns)
                        procedure['procedure_reasonCode'] = reasonCode.find('d:text', ns).attrib['value']
                        outcome = procedure_resource.find('d:outcome', ns)
                        procedure['procedure_outcome'] = outcome.find('d:text', ns).attrib['value']
                        complication = procedure_resource.find('d:complication', ns)
                        procedure['procedure_complication'] = complication.find('d:text', ns).attrib['value']
                        followUp = procedure_resource.find('d:followUp', ns)
                        procedure['procedure_followUp'] = followUp.find('d:text', ns).attrib['value']
                        note = procedure_resource.find('d:note', ns)
                        procedure['procedure_note'] = note.find('d:text', ns).attrib['value']
                        ProcedureModel.objects.create(
                            **procedure, encounter_identifier=encounter_instance)
            medication_statements = MedicationModel.objects.all().filter(encounter_identifier=encounter_instance)              
            if len(medication_statements) == 0:
                get_medication_statements = requests.get("http://hapi.fhir.org/baseR4/MedicationStatement?context.identifier=urn:trinhcongminh|" +
                                             encounter_identifier, headers={'Content-type': 'application/xml'})
                if get_medication_statements.status_code == 200 and 'entry' in get_medication_statements.content.decode('utf-8'):
                    get_root = ET.fromstring(
                        get_medication_statements.content.decode('utf-8'))
                    data['Medication'] = []
                    for entry in get_root.findall('d:entry', ns):
                        medication_statement = {}
                        resource = entry.find('d:resource', ns)
                        medication_resource = resource.find(
                            'd:MedicationStatement', ns)
                        medication_identifier = medication_resource.find(
                            'd:identifier', ns)
                        medication_statement['medication_identifier'] = medication_identifier.find(
                            'd:value', ns).attrib['value']
                        
                        medication = medication_resource.find(
                            'd:medicationCodeableConcept', ns)
                        medication_statement['medication_medication'] = medication.find('d:text', ns).attrib['value']
                        
                        medication_statement['medication_effective'] = medication_resource.find('d:effectiveDateTime', ns).attrib['value']
                        medication_statement['medication_dateAsserted'] = medication_resource.find('d:dateAsserted', ns).attrib['value']
                        reasonCode = medication_resource.find('d:reasonCode', ns)
                        medication_statement['medication_reasonCode'] = reasonCode.find('d:text', ns).attrib['value']
                        dosage = medication_resource.find('d:dosage', ns)
                        additional_instruction = dosage.find('d:additionalInstruction', ns)
                        if additional_instruction:
                            medication_statement['dosage_additional_instruction'] = additional_instruction.find('d:text', ns).attrib['value']
                        patient_instruction = dosage.find('d:patientInstruction', ns)
                        if patient_instruction:
                            medication_statement['dosage_patient_instruction'] = patient_instruction.find('d:text', ns).attrib['value']
                        timing = dosage.find('d:timing', ns)
                        repeat = timing.find('d:repeat', ns)
                        duration = repeat.find('d:duration', ns).attrib['value']
                        durationMax = repeat.find('d:durationMax', ns)
                        if durationMax:
                            duration = duration + '-' + durationMax.attrib['value']
                        durationUnit = repeat.find('d:durationUnit', ns).attrib['value']
                        duration = duration + ' ' + durationUnit
                        medication_statement['dosage_duration'] = duration
                        frequency = repeat.find('d:frequency', ns)
                        medication_statement['dosage_frequency'] = frequency.attrib['value']
                        period = repeat.find('d:period', ns).attrib['value']
                        periodMax = repeat.find('d:periodMax', ns)
                        if periodMax:
                            period = period + '-' + periodMax.attrib['value']
                        periodUnit = repeat.find('d:periodUnit', ns)
                        period = period + ' ' + periodUnit.attrib['value']
                        medication_statement['dosage_period'] = period
                        medication_statement['dosage_when'] = repeat.find('d:when', ns).attrib['value']
                        medication_statement['dosage_offset'] = repeat.find('d:offset', ns).attrib['value']
                        route = dosage.find('d:route', ns)
                        medication_statement['dosage_route'] = route.find('d:text', ns).attrib['value']
                        doseAndRate = dosage.find('d:doseAndRate', ns)
                        doseQuantity = doseAndRate.find('d:doseQuantity', ns)
                        quantity = doseQuantity.find('d:value', ns).attrib['value']
                        unit = doseQuantity.find('d:unit', ns).attrib['value']
                        medication_statement['dosage_quantity'] = quantity + ' ' + unit
                        MedicationModel.objects.create(
                            **medication_statement, encounter_identifier=encounter_instance)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        if data:
            return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services})
        else:
            return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        # else:
            # return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        instance = patient.objects.get(
            identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.identifier
        data['Patient']['name'] = instance.name
        data['Patient']['birthDate'] = instance.birthDate
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
        data['Patient']['birthDate'] = instance.birthDate
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
        return render(request, 'fhir/hanhchinh.html', {'group_name': group_name, 'user_name': user_name, 'data': data})


# class admin(View):
#     def get(self, request, group_name, user_name):
#         data = {
#             'employees': {},
#             'buildings': {},
#             'rooms': {},
#             'beds': {},
#             'facilities': {}
#         }
#         return render(request, 'admin/admin.html', {'group_name': group_name, 'user_name': user_name, 'data': data})

#     def post(self, request, group_name, user_name):
#         pass


class dangky(LoginRequiredMixin, View):
    login_url='/login/'
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


class hoibenh(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        condition_form = ConditionForm()
        condition = None
        try:
            condition = ConditionModel.objects.get(
                encounter_identifier=encounter)
            print(condition.condition_onset)
        except:
            print('somethingwrong')
            pass
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)

        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': condition_form, 'condition': condition, 'clinical': CONDITION_CLINICAL_CHOICES, 'severity': CONDITION_SEVERITY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        print(request.POST)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        if request.POST.get('condition_identifier'):
            condition_identifier = request.POST['condition_identifier']
            condition_instance = ConditionModel.objects.get(condition_identifier = condition_identifier)
            condition_instance.condition_code = request.POST['condition_code']
            condition_instance.condition_clinicalstatus = request.POST['condition_clinicalstatus']
            condition_instance.condition_onset = request.POST['condition_onset']
            condition_instance.condition_severity = request.POST['condition_severity']
            condition_instance.save()
        else:
            condition_identifier = encounter_identifier + '_' + \
                str(len(ConditionModel.objects.all().filter(
                    encounter_identifier=encounter_instance))+1)
            form = ConditionForm(request.POST)
            if form.is_valid():
                condition_n = form.save(commit=False)
                condition_n.encounter_identifier = encounter_instance
                condition_n.condition_identifier = condition_identifier
                form.save()
        condition = ConditionModel.objects.get(
            condition_identifier=condition_identifier)
        condition_form = ConditionForm()
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'condition': condition, 'clinical': CONDITION_CLINICAL_CHOICES, 'severity': CONDITION_SEVERITY_CHOICES, 'form': condition_form})


class xetnghiem(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance, service_category='laboratory')
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
                    encounter_identifier=encounter_instance)))
            service.service_authored = datetime.now().date()
            service.service_category = 'laboratory'
            service.service_requester = user_name
            form.save()
            print(service)
            print(service.service_code)
            createobservations(
                encounter_instance, service.service_identifier, service.service_code)
            print("save success")

        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance, service_category='laboratory')
        service_form = ServiceRequestForm()
        return render(request, 'fhir/xetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': service_form})


# class sieuam(View):
#     def get(self, request, group_name, user_name, encounter_id):
#         pass

#     def post(self, request, group_name, user_name, encounter_id):
#         pass


class service(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request):
        pass

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
            'identifier': encounter_identifier}, 'Service': {}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instances = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        observation_instances = ObservationModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        service_identifier = encounter_identifier + \
            '_' + str(len(service_instances) + 1)
        print(service_identifier)
        service = ServiceRequestModel(encounter_identifier=encounter_instance,
                                      service_identifier=service_identifier, service_category=request.POST['service_category'])
        if request.POST['service'] == 'lab1':
            service.service_location = 'room2'
            service.service_code = 'Xét nghiệm máu'
            service.save()
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_1', observation_name='Số lượng bạch cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='cells/mm3')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_2', observation_name='Bạch cầu Lympho', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_3', observation_name='Bạch cầu trung tính', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_4', observation_name='Bạch cầu mono', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_5', observation_name='Bạch cầu ái toan', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_6', observation_name='bạch cầu ái kiềm', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_7', observation_name='Số lượng hồng cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='cells/cm3')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_8', observation_name='Lượng huyết sắc tố trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='g/dl')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_9',
                                            observation_name='Tỷ lệ thể tích hồng cầu trên thể tích máu toàn phần', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_10', observation_name='Thể tích trung bình của một hồng cầu', observation_category=request.POST['service_category'], observation_valueunit='fl')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_11', observation_name='Lượng huyết sắc tố trung bình trong một hồng cầu', observation_category=request.POST['service_category'], observation_valueunit='pg')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_12',
                                            observation_name='Nồng độ trung bình của huyết sắc tố hemoglobin trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_13', observation_name='Độ phân bố kích thước hồng cầu', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_14', observation_name='Số lượng tiểu cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='cells/cm3')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_15', observation_name='Độ phân bố kích thước tiểu cầu', observation_category=request.POST['service_category'], observation_valueunit='%')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier + '_16',
                                            observation_name='Thể tích trung bình của tiểu cầu trong một thể tích máu', observation_category=request.POST['service_category'], observation_valueunit='fL')
        elif request.POST['service'] == 'lab2':
            service.service_location = 'room3'
            service.service_code = 'Xét nghiệm nước tiểu'
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_1', observation_name='Leukocytes', observation_category=request.POST['service_category'], observation_valueunit='LEU/UL')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_2', observation_name='Nitrate', observation_category=request.POST['service_category'], observation_valueunit='mg/dL')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_3', observation_name='Urobilinogen', observation_category=request.POST['service_category'], observation_valueunit='mmol/L')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_4', observation_name='Billirubin', observation_category=request.POST['service_category'], observation_valueunit='mmol/L')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_5', observation_name='Protein', observation_category=request.POST['service_category'], observation_valueunit='mg/dL')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_6', observation_name='Chỉ số pH', observation_category=request.POST['service_category'], observation_valueunit='')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_7', observation_name='Blood', observation_category=request.POST['service_category'], observation_valueunit='mg/dL')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_8', observation_name='Specific Gravity', observation_category=request.POST['service_category'], observation_valueunit='Cel')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_9', observation_name='Ketone', observation_category=request.POST['service_category'], observation_valueunit='mg/dL')
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_10', observation_name='Glucose', observation_category=request.POST['service_category'], observation_valueunit='Cel')
            service.save()
        elif request.POST['service'] == 'img1':
            service.service_location = 'room4'
            service.service_code = 'Chụp X-Quang'
            service.save()
        elif request.POST['service'] == 'img2':
            service.service_location = 'room5'
            service.service_code = 'Chụp MRI'
            service.save()
        elif request.POST['service'] == 'img3':
            service.service_location = 'room6'
            service.service_code = 'Siêu âm'
            service.save()

        data['Service']['identifier'] = service_identifier
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        observations = ObservationModel.objects.all().filter(
            service_identifier=service.service_identifier)
        return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})


class ketqua(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
            'identifier': encounter_identifier}, 'Service': {'identifier': service_identifier}}
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        observations = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        print(request.POST)
        observation_list = list(request.POST)
        print(observation_list)
        for i in range(1, len(observation_list)):
            observation = ObservationModel.objects.get(
                observation_identifier=observation_list[i])
            observation.observation_valuequantity = request.POST[observation_list[i]]
            observation.save()
        service = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        service.service_status = 'final'
        service.save()
        data = {'Patient': {'identifier': patient_identifier}, 'Encounter': {
            'identifier': encounter_identifier}, 'Service': {'identifier': service_identifier}}
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        observations = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        return render(request, 'fhir/xetnghiem.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'services': services, 'observations': observations})


class save(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Condition': []}
        patient = dt.query_patient(patient_identifier)
        get_encounter = dt.query_encounter(encounter_identifier)  
        print(get_encounter)   
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        encounter_instance.encounter_status = 'finished'
        encounter_instance.encounter_end = datetime.now()
        encounter_instance.save()
        data['Encounter']['identifier'] = encounter_identifier
        data['Encounter']['status'] = encounter_instance.encounter_status
        data['Encounter']['period'] = {}
        data['Encounter']['period']['start'] = encounter_instance.encounter_start.strftime(
            '%Y-%m-%dT%H:%M:%S+07:00')
        data['Encounter']['period']['end'] = encounter_instance.encounter_end.strftime(
            '%Y-%m-%dT%H:%M:%S+07:00')
        data['Encounter']['class'] = encounter_instance.encounter_class
        data['Encounter']['type'] = encounter_instance.encounter_type
        data['Encounter']['serviceType'] = encounter_instance.encounter_service
        data['Encounter']['priority'] = encounter_instance.encounter_priority
        data['Encounter']['reasonCode'] = encounter_instance.encounter_reason
        delta = encounter_instance.encounter_start.date(
        ) - encounter_instance.encounter_end.date()
        if delta.days == 0:
            data['Encounter']['length'] = '1'
        else:
            data['Encounter']['length'] = str(delta.days)
        if get_encounter:
            data['Encounter']['id'] = get_encounter['id']
        encounter_data = dt.create_encounter_resource(
            data['Encounter'], patient['id'], patient['name'])
        if get_encounter:
            put_encounter = requests.put("http://hapi.fhir.org/baseR4/Encounter/" + get_encounter['id'], headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
        else:
            post_encounter = requests.post("http://hapi.fhir.org/baseR4/Encounter/", headers={
                'Content-type': 'application/xml'}, data=encounter_data.decode('utf-8'))
            print(post_encounter.status_code)
        encounter = dt.query_encounter(encounter_identifier)
        if encounter:
            condition_instances = ConditionModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for condition_instance in condition_instances:
                put_condition = None
                post_condition = None
                condition = {}
                condition['identifier'] = condition_instance.condition_identifier
                condition['clinicalStatus'] = condition_instance.condition_clinicalstatus
                # condition['category'] = condition_instance.condition_category
                condition['severity'] = condition_instance.condition_severity
                condition['code'] = condition_instance.condition_code
                condition['onset'] = condition_instance.condition_onset.strftime(
                    '%Y-%m-%dT%H:%M:%S+07:00')
                
                get_condition = dt.query_condition(condition['identifier'])
                if get_condition:
                    condition['id'] = get_condition['id']
                condition_data = dt.create_condition_resource(
                    condition, patient['id'], patient['name'], encounter['id'])    
                if get_condition:
                    put_condition = requests.put("http://hapi.fhir.org/baseR4/Condition/"+get_condition['id'],headers={
                    'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
                else:
                    post_condition = requests.post("http://hapi.fhir.org/baseR4/Condition/", headers={
                    'Content-type': 'application/xml'}, data=condition_data.decode('utf-8'))
            service_instances = ServiceRequestModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for service_instance in service_instances:
                put_service = None
                post_service = None
                service_instance.service_status = 'completed'
                service_instance.save()
                service = {}
                service['identifier'] = service_instance.service_identifier
                service['status'] = service_instance.service_status
                service['category'] = service_instance.service_category
                service['intent'] = 'order'
                service['code'] = service_instance.service_code
                service['occurrence'] = service_instance.service_occurrence.strftime('%Y-%m-%d')
                service['authoredOn'] = service_instance.service_authored.strftime('%Y-%m-%d')
                get_service = dt.query_service(service['identifier'])
                if get_service:
                    service['id'] = get_service['id']
                service_data = dt.create_service_resource(
                    service, patient['id'], patient['name'], encounter['id'])
                if get_service:
                    put_service = requests.put("http://hapi.fhir.org/baseR4/ServiceRequest/" + get_service['id'], headers={
                    'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                else:
                    post_service = requests.post("http://hapi.fhir.org/baseR4/ServiceRequest/", headers={
                        'Content-type': 'application/xml'}, data=service_data.decode('utf-8'))
                if (put_service and put_service.status_code == 200) or (post_service and post_service.status_code == 201):
                    print(post_service)
                    service_query = dt.query_service(
                        service_instance.service_identifier)
                    print(service_query.get('id'))
                    service_observations = ObservationModel.objects.all().filter(
                        encounter_identifier=encounter_identifier, service_identifier=service_instance.service_identifier)
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
                        observation['valuequantity'] = observation_instance.observation_valuequantity
                        observation['valueunit'] = observation_instance.observation_valueunit
                        get_observation = dt.query_observation(observation['identifier'])
                        if get_observation:
                            observation['id'] = get_observation['id']
                        observation_data = dt.create_observation_resource(
                            observation, patient['id'], patient['name'], encounter['id'], service_query['id'])
                        if get_observation:
                            put_observation = requests.put("http://hapi.fhir.org/baseR4/Observation/" + get_observation['id'], headers={
                            'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                        else:
                            post_observation = requests.post("http://hapi.fhir.org/baseR4/Observation/", headers={
                                'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                else:
                    pass
            observation_instances = ObservationModel.objects.all().filter(
                encounter_identifier=encounter_instance, service_identifier='')
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
                observation['valuequantity'] = observation_instance.observation_valuequantity
                observation['valueunit'] = observation_instance.observation_valueunit
                get_observation = dt.query_observation(observation['identifier'])
                if get_observation:
                    observation['id'] = get_observation['id']
                observation_data = dt.create_observation_resource(
                    observation, patient['id'], patient['name'], encounter['id'])
                if get_observation:
                    put_observation = requests.put("http://hapi.fhir.org/baseR4/Observation/" + get_observation['id'], headers={
                    'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
                else:
                    post_observation = requests.post("http://hapi.fhir.org/baseR4/Observation/", headers={
                        'Content-type': 'application/xml'}, data=observation_data.decode('utf-8'))
            procedure_instances = ProcedureModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            for procedure_instance in procedure_instances:
                put_procedure = None
                post_procedure = None
                procedure = {}
                procedure['identifier'] = procedure_instance.procedure_identifier
                procedure['status'] = procedure_instance.procedure_status
                procedure['category'] = procedure_instance.procedure_category
                procedure['code'] = procedure_instance.procedure_code
                procedure['performedDateTime'] = procedure_instance.procedure_performedDateTime.strftime(
                    '%Y-%m-%dT%H:%M:%S+07:00')
                procedure['reasonCode'] = procedure_instance.procedure_reasonCode
                procedure['outcome'] = procedure_instance.procedure_outcome
                procedure['complication'] = procedure_instance.procedure_complication
                procedure['followUp'] = procedure_instance.procedure_followUp
                procedure['note'] = procedure_instance.procedure_note
                get_procedure = dt.query_procedure(procedure['identifier'])
                if get_procedure:
                    procedure['id'] = get_procedure['id']
                procedure_data = dt.create_procedure_resource(
                    procedure, patient['id'], patient['name'], encounter['id'])
                if get_procedure:
                    put_procedure = requests.put("http://hapi.fhir.org/baseR4/Procedure/" + get_procedure['id'], headers={
                    'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                else:
                    post_req = requests.post("http://hapi.fhir.org/baseR4/Procedure/", headers={
                        'Content-type': 'application/xml'}, data=procedure_data.decode('utf-8'))
                
            medication_instances = MedicationModel.objects.all().filter(
                encounter_identifier=encounter_instance)
            for medication_instance in medication_instances:
                put_medication = None
                post_medication = None
                medication = {}
                medication['identifier'] = medication_instance.medication_identifier
                medication['status'] = 'unknown'
                medication['medication'] = medication_instance.medication_medication
                medication['effective'] = medication_instance.medication_effective.strftime(
                    '%Y-%m-%d')
                medication['dateAsserted'] = medication_instance.medication_dateAsserted.strftime(
                    '%Y-%m-%d')
                medication['reasonCode'] = medication_instance.medication_reasonCode
                medication['additionalInstruction'] = medication_instance.dosage_additional_instruction
                medication['patientInstruction'] = medication_instance.dosage_patient_instruction
                medication['frequency'] = medication_instance.dosage_frequency
                medication['period'] = medication_instance.dosage_period
                medication['duration'] = medication_instance.dosage_duration
                medication['when'] = medication_instance.dosage_when
                medication['offset'] = medication_instance.dosage_offset
                medication['route'] = medication_instance.dosage_route
                medication['quantity'] = medication_instance.dosage_quantity
                get_medication = dt.query_medication(medication['identifier'])
                if get_medication:
                    medication['id'] = get_medication['id']
                medication_data = dt.create_medication_resource(
                    medication, patient['id'], patient['name'], encounter['id'])
                if get_medication:
                    put_medication = requests.put("http://hapi.fhir.org/baseR4/MedicationStatement/" + get_medication['id'], headers={
                    'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
                else:
                    post_medication = requests.post("http://hapi.fhir.org/baseR4/MedicationStatement/", headers={
                        'Content-type': 'application/xml'}, data=medication_data.decode('utf-8'))
            return HttpResponse('Success')
        else:
            return HttpResponse('Something Wrong')


class toanthan(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        observations = ObservationModel.objects.all().filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')
        print(observations)

        return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name,  'observations': observations})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        count = len(ObservationModel.objects.all().filter(
            encounter_identifier=encounter_instance))
        if request.POST['1']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Mạch', observation_category='vital-signs', observation_valuequantity=request.POST['1'], observation_valueunit='lần/ph')
        if request.POST['2']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Nhiệt độ', observation_category='vital-signs', observation_valuequantity=request.POST['2'], observation_valueunit='Cel')
        if request.POST['3']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Huyết áp tâm thu', observation_category='vital-signs', observation_valuequantity=request.POST['3'].split('/')[0], observation_valueunit='mmHg')
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Huyết áp tâm trương', observation_category='vital-signs', observation_valuequantity=request.POST['3'].split('/')[1], observation_valueunit='mmHg')
        if request.POST['4']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Nhịp thở', observation_category='vital-signs', observation_valuequantity=request.POST['4'], observation_valueunit='lần/ph')
        if request.POST['5']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_status='final', observation_code='Cân nặng', observation_category='vital-signs', observation_valuequantity=request.POST['5'], observation_valueunit='kg')
        observations = ObservationModel.objects.all().filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')

        return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'observations': observations})


class thuthuat(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        return render(request, 'fhir/thuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': procedure_form, 'procedures': procedures, 'procedure_category': PROCEDURE_CATEGORY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = ProcedureForm(request.POST)
        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.encounter_identifier = encounter_instance
            procedure.procedure_identifier = encounter_instance.encounter_identifier + \
                '_' + str(len(ProcedureModel.objects.all().filter(
                    encounter_identifier=encounter_instance)) + 1)
            print(encounter_instance.encounter_identifier +
                  '_' + str(len(ProcedureModel.objects.all().filter(
                      encounter_identifier=encounter_instance)) + 1))
            procedure.procedure_status = 'preparation'
            form.save()
        procedures = ProcedureModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        procedure_form = ProcedureForm()
        return render(request, 'fhir/thuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name,  'form': procedure_form, 'procedures': procedures, 'procedure_category': PROCEDURE_CATEGORY_CHOICES})


class chitietthuthuat(LoginRequiredMixin, View):
    login_url='/login/'
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
            procedure.procedure_performedDateTime = datetime.now()
            form.save()
            print('save success')
        return render(request, 'fhir/chitietthuthuat.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'procedure': procedure_instance, 'form': form})


class thuoc(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        medications = MedicationModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        medication_form = MedicationForm()
        return render(request, 'fhir/thuoc.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'medications': medications, 'form': medication_form})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = MedicationForm(request.POST)
        print(form)
        if form.is_valid():
            medication = form.save(commit=False)
            medication.encounter_identifier = encounter_instance
            medication.medication_identifier = encounter_instance.encounter_identifier + '_' + \
                str(len(MedicationModel.objects.all().filter(
                    encounter_identifier=encounter_instance)) + 1)
            medication.medication_dateAsserted = datetime.now().date()
            form.save()
            print('save success')
        medications = MedicationModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        medication_form = MedicationForm()
        return render(request, 'fhir/thuoc.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'medications': medications, 'form': medication_form})


class chitietxetnghiem(LoginRequiredMixin, View):
    login_url='/login/'
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        print(service_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        observation_instances = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        print(observation_instances)
        return render(request, 'fhir/chitietxetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'service': service_instance, 'observations': observation_instances})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier, service_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        print(service_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        service_instance = ServiceRequestModel.objects.get(
            service_identifier=service_identifier)
        observation_list = list(request.POST)
        print(observation_list)
        for i in range(1, len(observation_list)):
            observation = ObservationModel.objects.get(
                observation_identifier=observation_list[i])
            observation.observation_valuequantity = request.POST[observation_list[i]]
            observation.observation_performer = user_name
            observation.observation_status = 'final'
            observation.save()
        observation_instances = ObservationModel.objects.all().filter(
            service_identifier=service_identifier)
        service_instance.service_status = 'completed'
        service_instance.save()
        return render(request, 'fhir/chitietxetnghiem.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'service': service_instance, 'observations': observation_instances})


service_dict = {
    'Full Blood Count': {
        'WBC': {'unit': '/L'},
        'RBC': {'unit': '/L'},
        'HAEMOGLOBIN': {'unit': 'g/dl'},
        'PCV': {'unit': '%'},
        'MCV': {'unit': 'fl'},
        'MCH': {'unit': 'pg'},
        'MCHC': {'unit': 'g/dl'},
        'PLATELET COUNT': {'unit': '/L'},
        'NEUTROPHIL': {'unit': '%'},
        'LYMPHOCYTE': {'unit': '%'},
        'MONOCYTE': {'unit': '%'},
        'EOSINOPHIL': {'unit': '%'},
        'BASOPHIL': {'unit': '%'},
        'RDW-SD': {'unit': 'fl'},
        'RDW-CV': {'unit': '%'},
        'PWD': {'unit': 'fl'},
        'MPV': {'unit': 'fl'},
        'P-LCR': {'unit': '%'},
        'PCT': {'unit': '%'}
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


def createobservations(encounter_instance, service_identifier, service_name):
    request_observations = service_dict.get(service_name, None)
    i = 1
    print(request_observations)
    if request_observations:
        for key, value in request_observations.items():
            ObservationModel.objects.create(encounter_identifier=encounter_instance, service_identifier=service_identifier, observation_identifier=service_identifier +
                                            '_' + str(i), observation_code=key, observation_category='laboratory', observation_valueunit=value['unit'])
            i += 1
    else:
        print('no valid data')
