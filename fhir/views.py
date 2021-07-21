from django.shortcuts import render
from django.http import HttpResponse, request
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
from .forms import Encounter, UserForm
from django.shortcuts import get_object_or_404
# Create your views here.

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
    user_id = user.user_identifier
    if user:
        patient['name'] = user.full_name
        patient['gender'] = user.gender
        patient['birthDate'] = user.birth_date
        patient['address'] = [{'address': user.home_address, 'use': 'home'},
                              {'address': user.work_address, 'use': 'work'}]
        patient['identifier'] = user.user_identifier
        message = 'Đây là hồ sơ của bạn'
    else:
        message = 'Bạn chưa có hồ sơ khám bệnh'
    return render(request, 'fhir/patient/display.html', {'group_name': group_name, 'user_name': user_name, 'id': user_id, 'patient': patient, 'message': message})


class register(View):
    def get(self, request, group_name, user_name):
        EHRform = EHRCreationForm()
        User = get_user_model()

        return render(request, 'fhir/doctor/create.html', {'group_name': group_name, 'user_name': user_name, 'form': EHRCreationForm})

    def post(self, request, group_name, user_name):
        User = get_user_model()
        if request.POST:
            data = {'Patient': {}}
            data['Patient']['name'] = request.POST['full_name']
            data['Patient']['gender'] = request.POST['gender']
            data['Patient']['birthDate'] = request.POST['birth_date']
            data['Patient']['address'] = [{'address': request.POST['home_address'], 'use': 'home'},
                                          {'address': request.POST['work_address'], 'use': 'work'}]
            data['Patient']['identifier'] = request.POST['user_identifier']

            # xml_data, data = handlers.register_ehr(patient, id_system)
            patient = dt.create_patient_resource(data['Patient'])
            try:
                instance = User.objects.get(
                    user_identifier=patient['identifier'])
                # instance = get_object_or_404(
                #     User, user_identifier=patient['identifier'])
            except User.DoesNotExist:
                user = User.objects.create_user(
                    patient['identifier'], 'test@gmail.com', 'nam12345')
                user.save()
                # form = EHRCreationForm(request.POST or None)
                # if form.is_valid():
                #     user_n = form.save(commit=False)
                #     user_n.username = patient['identifier']
                #     user_n.set_password('nam12345')
                #     user_n.group_name = 'patient'
                #     user_n.save()
                #     form.save()
                # if patient:
                #     hapi_request = requests.post("http://hapi.fhir.org/baseR4/Patient/", headers={
                #         'Content-type': 'application/xml'}, data=patient.decode('utf-8'))
                # instance = get_object_or_404(
                #     User, user_identifier=data['Patient']['identifier'])
                # form = EHRCreationForm(request.POST or None, instance=instance)
                # if form.is_valid():
                #     form.save()
                # name = instance.username
            return render(request, 'fhir/doctor/display.html', {'group_name': group_name, 'user_name': user_name, 'data': data})
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
                data['Patient']['identifier'])
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
        data = {'Patient': {}, 'Encounter': {}}
        if request.POST:
            data['Patient'] = dt.query_patient(request.POST['identifier'])
            if data['Patient']:
                get_encounter = requests.get("http://hapi.fhir.org/baseR4/Encounter?subject.identifier=urn:trinhcongminh|" +
                                             request.POST['identifier'], headers={'Content-type': 'application/xml'})
                if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
                    get_root = ET.fromstring(
                        get_encounter.content.decode('utf-8'))
                    data['Encounter'] = []
                    for entry in get_root.findall('d:entry', ns):
                        resource = entry.find('d:resource', ns)
                        encounter_resource = resource.find('d:Encounter', ns)
                        encounter_id = encounter_resource.find(
                            'd:id', ns).attrib['value']
                        _class = encounter_resource.find('d:class', ns)
                        class_value = _class.find('d:code', ns).attrib['value']
                        status = encounter_resource.find(
                            'd:status', ns).attrib['value']
                        period = encounter_resource.find('d:period', ns)
                        start_date = period.find('d:start', ns).attrib['value']
                        start_date = dt.getdatetime(start_date)
                        end_date = None
                        if period.find('d:end', ns) != None:
                            end_date = period.find('d:end', ns).attrib['value']
                            end_date = dt.getdatetime(end_date)
                        data['Encounter'].append({'id': encounter_id, 'class': class_value, 'status': status, 'period': {
                                                 'start': start_date, 'end': end_date}})
                data['encounter_type'] = 'list'
                return render(request, 'fhir/doctor/display.html', {'message': 'Da tim thay', 'data': data, 'group_name': group_name, 'user_name': user_name})
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database', 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Please enter an identifier', 'group_name': group_name, 'user_name': user_name})


class display_observation(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        data['Patient'] = dt.query_patient(patient_identifier)
        data['Encounter'] = dt.get_encounter(encounter_id)
        if data['Encounter']:
            data['Observation'] = dt.get_observation(encounter_id)
            if data['Observation']:
                return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})
            else:
                return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(View):
    def get(self, request, group_name, user_name):
        return render(request, 'fhir/doctor/encounter.html', {'group_name': group_name, 'user_name': user_name})


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
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        form = Encounter()
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'id': encounter_id}, 'dangky': {}, 'form': form}
        return render(request, 'fhir/dangky.html', {'data': data, 'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name, encounter_id):
        pass


class hanhchinh(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        data['Patient'] = dt.query_patient(patient_identifier)
        data['Encounter'] = dt.get_encounter(encounter_id)
        if data['Encounter']:
            data['Observation'] = dt.get_observation(encounter_id)
            if data['Observation']:
                return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})
            else:
                return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name, encounter_id):
        pass


class hoibenh(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'id': encounter_id}}
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})

    def post(self, request, group_name, user_name, encounter_id):
        pass


class xetnghiem(View):
    def get(self, request, group_name, user_name, encounter_id):
        pass

    def post(self, request, group_name, user_name, encounter_id):
        pass


class sieuam(View):
    def get(self, request, group_name, user_name, encounter_id):
        pass

    def post(self, request, group_name, user_name, encounter_id):
        pass
