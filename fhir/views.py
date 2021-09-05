from django.shortcuts import render
from django.http import HttpResponse, request, HttpResponseRedirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import xml.etree.ElementTree as ET
import requests
import uuid
from lib import dttype as dt
from login.forms import UserCreationForm
from handlers import handlers
from fhir.forms import EHRCreationForm
from .models import EncounterModel, ServiceRequestModel, UserModel, ConditionModel, ObservationModel
from .forms import EncounterForm, ConditionForm, ObservationForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.template.defaulttags import register
# Create your views here.

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


CLASS_CHOICES = {
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
TYPE_CHOICES = {
    '1': 'Bệnh án nội khoa',
    '2': 'Bệnh án ngoại khoa',
    '3': 'Bệnh án phụ khoa',
    '4': 'Bệnh án sản khoa'
}
PRIORITY_CHOICES = {
    'A': 'ASAP',
    'EL': 'Tự chọn',
    'EM': 'Khẩn cấp',
    'P': 'Trước',
    'R': 'Bình thường',
    'S': 'Star'
}
CLINICAL_CHOICES = {
    'active': 'Active',
    'inactive': 'Inactive',
    'recurrence': 'Recurrence',
    'relapse': 'Relapse',
    'remission': 'Remission',
    'resolved': 'Resolves'
}
SEVERITY_CHOICES = {
    '24484000': 'Nặng',
    '6736007': 'Vừa',
    '255604002': 'Nhẹ'
}
id_system = "urn:trinhcongminh"

ns = {'d': "http://hl7.org/fhir"}


@login_required(login_url='/login/')
def user_app(request, group_name, user_name):
    User = get_user_model()
    group_name = User.objects.get(username=user_name).group_name
    page = 'fhir/' + str(group_name) + '.html'
    return render(request, page, {'group_name': group_name, 'user_name': user_name})


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
    data['Encounter'] = EncounterModel.objects.all().filter(
        user_identifier=patient_identifier)
    if data['Encounter']:
        data['encounter_type'] = 'list'
    img_dir = f'/static/img/patient/{patient_identifier}.jpg'
    # pass
    return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data, 'img_dir': img_dir, 'form': encounter_form})


class register(View):
    def get(self, request, group_name, user_name):
        EHRform = EHRCreationForm()
        User = get_user_model()

        return render(request, 'fhir/doctor/create.html', {'group_name': group_name, 'user_name': user_name, 'form': EHRCreationForm})

    def post(self, request, group_name, user_name):
        User = get_user_model()
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
                data['Patient']['id'] = dt.query_patient(data['Patient']['identifier'])['id']
            patient = dt.create_patient_resource(data['Patient'])
            print(patient)
            if data['Patient'].get('id'):
                print("http://hapi.fhir.org/baseR4/Patient/" + data['Patient']['id'])
                put_patient = requests.put("http://hapi.fhir.org/baseR4/Patient/" + data['Patient']['id'], headers={'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
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
                print('create new ressource')
                post_req = requests.post("http://hapi.fhir.org/baseR4/Patient/", headers={
                    'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
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
                        return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data})
                    else:
                        return HttpResponse("Something wrong when trying to register patient")
        else:
            return HttpResponse("Please enter your information")



class upload(View):
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


class search(View):
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
                data['Patient']['birthDate'] = datetime.strftime(instance.birthDate, "%d-%m-%Y")
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
                return render(request, 'fhir/doctor/search.html', {'message': 'Da tim thay', 'data': data, 'group_name': group_name, 'user_name': user_name, 'form':encounter_form})
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database', 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Please enter an identifier', 'group_name': group_name, 'user_name': user_name})


class hanhchinh(View):
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
            print(conditions)
            if len(conditions) == 0:
                get_condition = requests.get("http://hapi.fhir.org/baseR4/Condition?encounter.identifier=urn:trinhcongminh|" +
                                             encounter_identifier, headers={'Content-type': 'application/xml'})
                print(get_condition.content)
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
                                observation['observation_name'] = code.find(
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
                        observation['observation_name'] = code.find(
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
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        if data:
            return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services})
        else:
            return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        # else:
            # return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(View):
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

class admin(View):
    def get(self, request, group_name, user_name):
        data = {
            'employees': {},
            'buildings': {},
            'rooms': {},
            'beds': {},
            'facilities': {}
        }
        return render(request, 'admin/admin.html', {'group_name': group_name, 'user_name': user_name, 'data': data})

    def post(self, request, group_name, user_name):
        pass


class dangky(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Encounter_Info': {}}
        encounter_form = EncounterForm()
        data['Encounter_Info'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        data['Patient']['identifier'] = patient_identifier
        data['Encounter']['identifier'] = encounter_identifier
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=data['Encounter_Info'])
        return render(request, 'fhir/dangky.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'form': encounter_form, 'services': services, 'class': CLASS_CHOICES, 'priority': PRIORITY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Encounter_Info': {}}
        data['Patient']['identifier'] = patient_identifier
        patient = get_user_model()
        instance = patient.objects.get(
            identifier=patient_identifier)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        form = EncounterForm(request.POST, encounter_instance)
        if form.is_valid():
            encounter_n = form.save(commit=False)
            encounter_n.encounter_identifier = encounter_identifier
            encounter_n.user_identifier = instance
            encounter_n.encounter_submitted = True
            form.save()
        data['Encounter']['identifier'] = encounter_identifier
        data['Encounter_Info'] = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        return render(request, 'fhir/dangky.html', {'group_name': group_name, 'user_name': user_name, 'data': data})


class hoibenh(View):
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
        
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'form': condition_form, 'condition': condition, 'clinical': CLINICAL_CHOICES, 'severity': SEVERITY_CHOICES})

    def post(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        print(request.POST)
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        condition_identifier = encounter_identifier + '_' + \
            str(len(ConditionModel.objects.all().filter(
                encounter_identifier=encounter_instance))+1)
        form = ConditionForm(request.POST, encounter_instance)
        if form.is_valid():
            condition_n = form.save(commit=False)
            condition_n.encounter_identifier = encounter_instance
            condition_n.condition_identifier = condition_identifier
            form.save()
        condition = ConditionModel.objects.get(
            condition_identifier=condition_identifier)
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'condition': condition, 'clinical': CLINICAL_CHOICES, 'severity': SEVERITY_CHOICES})


class xetnghiem(View):
    def get(self, request, group_name, user_name, encounter_identifier):
        pass

    def post(self, request, group_name, user_name, encounter_identifier):
        pass


class sieuam(View):
    def get(self, request, group_name, user_name, encounter_id):
        pass

    def post(self, request, group_name, user_name, encounter_id):
        pass


class service(View):
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


class ketqua(View):
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


class save(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {}, 'Encounter': {}, 'Condition': []}
        patient = dt.query_patient(patient_identifier)
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
        post_encounter = dt.create_encounter_resource(
            data['Encounter'], patient['id'], patient['name'])
        post_req = requests.post("http://hapi.fhir.org/baseR4/Encounter/", headers={
                                 'Content-type': 'application/xml'}, data=post_encounter.decode('utf-8'))
        encounter = dt.query_encounter(encounter_identifier)
        print(encounter['id'])
        if encounter:
            condition_instances = ConditionModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for condition_instance in condition_instances:
                condition = {}
                condition['identifier'] = condition_instance.condition_identifier
                condition['clinicalStatus'] = condition_instance.condition_clinicalstatus
                # condition['category'] = condition_instance.condition_category
                condition['severity'] = condition_instance.condition_severity
                condition['code'] = condition_instance.condition_code
                condition['onset'] = condition_instance.condition_onset.strftime(
                    '%Y-%m-%dT%H:%M:%S+07:00')
                post_condition = dt.create_condition_resource(
                    condition, patient['id'], patient['name'], encounter['id'])
                print(post_condition)
                post_req = requests.post("http://hapi.fhir.org/baseR4/Condition/", headers={
                                         'Content-type': 'application/xml'}, data=post_condition.decode('utf-8'))
            service_instances = ServiceRequestModel.objects.all().filter(
                encounter_identifier=encounter_identifier)
            for service_instance in service_instances:
                service_instance.service_status = 'completed'
                service_instance.save()
                service = {}
                service['identifier'] = service_instance.service_identifier
                service['status'] = service_instance.service_status
                service['category'] = service_instance.service_category
                service['intent'] = 'order'
                service['code'] = service_instance.service_code
                post_service = dt.create_service_resource(
                    service, patient['id'], patient['name'], encounter['id'])
                post_req = requests.post("http://hapi.fhir.org/baseR4/ServiceRequest/", headers={
                                         'Content-type': 'application/xml'}, data=post_service.decode('utf-8'))
                if post_req.status_code == 201:
                    print(post_service)
                    service_query = dt.query_service(
                        service_instance.service_identifier)
                    print(service_query['id'])
                    service_observations = ObservationModel.objects.all().filter(
                        encounter_identifier=encounter_identifier, service_identifier=service_instance.service_identifier)
                    for observation_instance in service_observations:
                        observation = {}
                        observation['identifier'] = observation_instance.observation_identifier
                        observation['status'] = observation_instance.observation_status
                        observation['code'] = observation_instance.observation_name
                        observation['category'] = observation_instance.observation_category
                        observation['effective'] = observation_instance.observation_effective.strftime(
                            '%Y-%m-%dT%H:%M:%S+07:00')
                        observation['valuequantity'] = observation_instance.observation_valuequantity
                        observation['valueunit'] = observation_instance.observation_valueunit
                        post_observation = dt.create_observation_resource(
                            observation, patient['id'], patient['name'], encounter['id'], service_query['id'])
                        print(post_observation)
                        post_req = requests.post("http://hapi.fhir.org/baseR4/Observation/", headers={
                                                 'Content-type': 'application/xml'}, data=post_observation.decode('utf-8'))
                else:
                    pass
            observation_instances = ObservationModel.objects.all().filter(
                encounter_identifier=encounter_instance, service_identifier='')
            for observation_instance in observation_instances:
                observation = {}
                observation['identifier'] = observation_instance.observation_identifier
                observation['status'] = observation_instance.observation_status
                observation['code'] = observation_instance.observation_name
                observation['category'] = observation_instance.observation_category
                observation['effective'] = observation_instance.observation_effective.strftime(
                    '%Y-%m-%dT%H:%M:%S+07:00')
                observation['valuequantity'] = observation_instance.observation_valuequantity
                observation['valueunit'] = observation_instance.observation_valueunit
                post_observation = dt.create_observation_resource(
                    observation, patient['id'], patient['name'], encounter['id'])
                print(post_observation)
                post_req = requests.post("http://hapi.fhir.org/baseR4/Observation/", headers={
                                         'Content-type': 'application/xml'}, data=post_observation.decode('utf-8'))
            return HttpResponse('Success')
        else:
            return HttpResponse('Something Wrong')


class toanthan(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_identifier):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'identifier': encounter_identifier}}
        encounter_instance = EncounterModel.objects.get(
            encounter_identifier=encounter_identifier)
        observations = ObservationModel.objects.all().filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')
        print(observations)
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_instance)
        return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'observations': observations})

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
                count), observation_name='Mạch', observation_category='vital-signs', observation_valuequantity=request.POST['1'], observation_valueunit='lần/ph')
        if request.POST['2']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_name='Nhiệt độ', observation_category='vital-signs', observation_valuequantity=request.POST['2'], observation_valueunit='Cel')
        if request.POST['3']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_name='Huyết áp tâm thu', observation_category='vital-signs', observation_valuequantity=request.POST['3'].split('/')[0], observation_valueunit='mmHg')
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_name='Huyết áp tâm trương', observation_category='vital-signs', observation_valuequantity=request.POST['3'].split('/')[1], observation_valueunit='mmHg')
        if request.POST['4']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_name='Nhịp thở', observation_category='vital-signs', observation_valuequantity=request.POST['4'], observation_valueunit='lần/ph')
        if request.POST['5']:
            count += 1
            ObservationModel.objects.create(encounter_identifier=encounter_instance, observation_identifier=encounter_identifier + '_' + str(
                count), observation_name='Cân nặng', observation_category='vital-signs', observation_valuequantity=request.POST['5'], observation_valueunit='kg')
        observations = ObservationModel.objects.all().filter(
            encounter_identifier=encounter_instance, observation_category='vital-signs')
        services = ServiceRequestModel.objects.all().filter(
            encounter_identifier=encounter_identifier)
        return render(request, 'fhir/toanthan.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services': services, 'observations': observations})
