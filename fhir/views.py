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
from .models import EncounterModel, ServiceRequestModel, UserModel, ConditionModel, ObservationModel
from .forms import EncounterForm, ConditionForm, ObservationForm
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
                    user_identifier=data['Patient']['identifier'])
                # instance = get_object_or_404(
                #     User, user_identifier=patient['identifier'])
            except User.DoesNotExist:
                # user = User.objects.create_user(
                    # data['Patient']['identifier'], 'test@gmail.com', 'nam12345')
                # user.save()
                form = EHRCreationForm(request.POST or None)
                if form.is_valid():
                    user_n = form.save(commit=False)
                    user_n.username = data['Patient']['identifier']
                    user_n.set_password('nam12345')
                    user_n.group_name = 'patient'
                    user_n.save()
                    form.save()
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
        data = {'Patient': {}, 'Encounter': []}
        patient = get_user_model()
        if request.POST:
            try:
                instance = patient.objects.get(
                user_identifier=request.POST['identifier'])
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
                data['Patient']['identifier'] = instance.user_identifier
                data['Patient']['name'] = instance.full_name
                data['Patient']['birthDate'] = instance.birth_date
                data['Patient']['gender'] = instance.gender
                data['Patient']['address'] = [{'address':instance.home_address,'use':'home'}]
                if instance.work_address:
                    data['Patient']['address'].append({'address': instance.work_address, 'use':'work'})
                encounter_instances = EncounterModel.objects.all().filter(user_identifier=instance.user_identifier)
                print(encounter_instances)
                if encounter_instances:
                    for encounter in encounter_instances:
                        encounter_id = encounter.encounter_id
                        start_date = encounter.start_date
                        status = encounter.encounter_status
                        end_date = None
                        if encounter.end_date:
                            end_date = encounter.end_date
                        class_value = 'new'
                        if encounter.class_select:
                            class_value = encounter.class_select
                        data['Encounter'].append({'id': encounter_id, 'class': class_value, 'status': status, 'period': {
                                                    'start': start_date, 'end': end_date}})
            except patient.DoesNotExist:
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
            if data:
                data['encounter_type'] = 'list'
                return render(request, 'fhir/doctor/display.html', {'message': 'Da tim thay', 'data': data, 'group_name': group_name, 'user_name': user_name})
            else:
                return render(request, 'fhir/doctor.html', {'message': 'Patient not found in database', 'group_name': group_name, 'user_name': user_name})
        else:
            return render(request, 'fhir/doctor.html', {'message': 'Please enter an identifier', 'group_name': group_name, 'user_name': user_name})


class hanhchinh(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
        try:
            instance = patient.objects.get(
                user_identifier=patient_identifier)
            # instance = get_object_or_404(
            #     User, user_identifier=patient['identifier'])
            data['Patient']['identifier'] = instance.user_identifier
            data['Patient']['name'] = instance.full_name
            data['Patient']['birthDate'] = instance.birth_date
            data['Patient']['gender'] = instance.gender
            data['Patient']['address'] = [{'address':instance.home_address,'use':'home'}]
            if instance.work_address:
                data['Patient']['address'].append({'address': instance.work_address, 'use':'work'})            

        except patient.DoesNotExist:
            
        
            data['Patient'] = dt.query_patient(patient_identifier)
            data['Encounter'] = dt.get_encounter(encounter_id)
            if data['Encounter']:
                data['Observation'] = dt.get_observation(encounter_id)
        data['Encounter']['id'] = encounter_id
        services = ServiceRequestModel.objects.all().filter(encounter_id = encounter_id)
        if data:
            return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services':services})
        else:
            return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
        # else:
            # return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})


class encounter(View):
    def get(self, request, group_name, user_name, patient_identifier):
        patient = get_user_model()
        data = {'Patient': {}, 'Encounter': {}, 'Observation': []}        
        instance = patient.objects.get(
            user_identifier=patient_identifier)
        # instance = get_object_or_404(
        #     User, user_identifier=patient['identifier'])
        data['Patient']['identifier'] = instance.user_identifier
        data['Patient']['name'] = instance.full_name
        data['Patient']['birthDate'] = instance.birth_date
        data['Patient']['gender'] = instance.gender
        data['Patient']['address'] = [{'address':instance.home_address,'use':'home'}]
        if instance.work_address:
            data['Patient']['address'].append({'address': instance.work_address, 'use':'work'})        
        newencounter = EncounterModel.objects.create(user_identifier=instance)
        data['Encounter']['id'] = newencounter.encounter_id
        return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})


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
        data = {'Patient': {}, 'Encounter': {}, 'Encounter_Info':{}}
        encounter_form = EncounterForm()
        data['Encounter_Info'] = EncounterModel.objects.get(encounter_id = encounter_id)
        data['Patient']['identifier'] = patient_identifier        
        data['Encounter']['id'] = encounter_id
        services = ServiceRequestModel.objects.all().filter(encounter_id = encounter_id)
        return render(request, 'fhir/dangky.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'form':encounter_form,'services':services})

    def post(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient':{}, 'Encounter':{}, 'Encounter_Info': {}}
        data['Patient']['identifier'] = patient_identifier
        patient = get_user_model()
        instance = patient.objects.get(
        user_identifier=patient_identifier)
        encounter = EncounterModel.objects.get(encounter_id = encounter_id)
        form = EncounterForm(request.POST, encounter)
        if form.is_valid():           
            encounter_n = form.save(commit=False)
            encounter_n.encounter_id = encounter_id
            encounter_n.user_identifier = instance
            encounter_n.submitted = True
            form.save()
        data['Encounter']['id'] = encounter_id
        data['Encounter_Info'] = EncounterModel.objects.get(encounter_id = encounter_id)
        return render(request, 'fhir/dangky.html', {'group_name': group_name, 'user_name': user_name,'data': data})
            



# class hanhchinh(View):
#     def get(self, request, group_name, user_name, patient_identifier, encounter_id):
#         data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
#         data['Patient'] = dt.query_patient(patient_identifier)
#         data['Encounter'] = dt.get_encounter(encounter_id)
#         if data['Encounter']:
#             data['Observation'] = dt.get_observation(encounter_id)
#             if data['Observation']:
#                 return render(request, 'fhir/hanhchinh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})
#             else:
#                 return render(request, 'fhir/doctor.html', {'message': "No data found", 'group_name': group_name, 'user_name': user_name})
#         else:
#             return render(request, 'fhir/doctor.html', {'message': 'Something wrong', 'group_name': group_name, 'user_name': user_name})



class hoibenh(View):
    def get(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient': {'identifier': patient_identifier},
                'Encounter': {'id': encounter_id}}
        condition_form = ConditionForm()
        services = ServiceRequestModel.objects.all().filter(encounter_id = encounter_id)
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name, 'services':services, 'form': condition_form})

    def post(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient': {'identifier': patient_identifier},
        'Encounter': {'id': encounter_id}}
        encounter_instance = EncounterModel.objects.get(encounter_id = encounter_id)
        form = ConditionForm(request.POST, encounter)
        if form.is_valid():           
            condition_n = form.save(commit=False)
            condition_n.encounter_id = encounter_instance
            form.save()
        data['Condition'] = ConditionModel.objects.get(encounter_id = encounter_id)
        return render(request, 'fhir/hoibenh.html', {'data': data, 'group_name': group_name, 'user_name': user_name})


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

class service(View):
    def get(self, request):
        pass
    
    def post(self, request, group_name, user_name, patient_identifier, encounter_id):
        data = {'Patient':{'identifier': patient_identifier}, 'Encounter':{'id':encounter_id}}
        encounter_instance = EncounterModel.objects.get(encounter_id = encounter_id)
        service = ServiceRequestModel(encounter_id=encounter_instance, request_category=request.POST['service_category'])
        
        if request.POST['service'] == 'vital':            
            service.request_location = 'room1'
            service.request_description = 'Khám tổng quát'
            service.save()
            ObservationModel.objects.create(service_id=service,name='Nhiệt độ',category=request.POST['service_category'], valueunit='Cel')
            ObservationModel.objects.create(service_id=service,name='Cân nặng',category=request.POST['service_category'], valueunit='kg')
            ObservationModel.objects.create(service_id=service,name='Nhịp thở',category=request.POST['service_category'], valueunit='mmHg')
            ObservationModel.objects.create(service_id=service,name='Huyết áp tâm thu',category=request.POST['service_category'], valueunit='mmHg')
            ObservationModel.objects.create(service_id=service,name='Huyết áp tâm trương',category=request.POST['service_category'], valueunit='breaths/minute')
        elif request.POST['service'] == 'lab1':        
            service.request_location = 'room2'
            service.request_description = 'Xét nghiệm máu'
            service.save()
            ObservationModel.objects.create(service_id=service,name='Số lượng bạch cầu trong một thể tích máu',category=request.POST['service_category'], valueunit='cells/mm3')
            ObservationModel.objects.create(service_id=service,name='Bạch cầu Lympho',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Bạch cầu trung tính',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Bạch cầu mono',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Bạch cầu ái toan',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='bạch cầu ái kiềm',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Số lượng hồng cầu trong một thể tích máu',category=request.POST['service_category'], valueunit='cells/cm3')
            ObservationModel.objects.create(service_id=service,name='Lượng huyết sắc tố trong một thể tích máu',category=request.POST['service_category'], valueunit='g/dl')
            ObservationModel.objects.create(service_id=service,name='Tỷ lệ thể tích hồng cầu trên thể tích máu toàn phần',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Thể tích trung bình của một hồng cầu',category=request.POST['service_category'], valueunit='fl')
            ObservationModel.objects.create(service_id=service,name='Lượng huyết sắc tố trung bình trong một hồng cầu',category=request.POST['service_category'], valueunit='pg')
            ObservationModel.objects.create(service_id=service,name='Nồng độ trung bình của huyết sắc tố hemoglobin trong một thể tích máu',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Độ phân bố kích thước hồng cầu',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Số lượng tiểu cầu trong một thể tích máu',category=request.POST['service_category'], valueunit='cells/cm3')
            ObservationModel.objects.create(service_id=service,name='Độ phân bố kích thước tiểu cầu',category=request.POST['service_category'], valueunit='%')
            ObservationModel.objects.create(service_id=service,name='Thể tích trung bình của tiểu cầu trong một thể tích máu',category=request.POST['service_category'], valueunit='fL')
        elif request.POST['service'] == 'lab2':
            service.request_location = 'room3'
            service.request_description = 'Xét nghiệm nước tiểu'
            ObservationModel.objects.create(service_id=service,name='Leukocytes',category=request.POST['service_category'], valueunit='LEU/UL')
            ObservationModel.objects.create(service_id=service,name='Nitrate',category=request.POST['service_category'], valueunit='mg/dL')
            ObservationModel.objects.create(service_id=service,name='Urobilinogen',category=request.POST['service_category'], valueunit='mmol/L')
            ObservationModel.objects.create(service_id=service,name='Billirubin',category=request.POST['service_category'], valueunit='mmol/L')
            ObservationModel.objects.create(service_id=service,name='Protein',category=request.POST['service_category'], valueunit='mg/dL')
            ObservationModel.objects.create(service_id=service,name='Chỉ số pH',category=request.POST['service_category'], valueunit='')
            ObservationModel.objects.create(service_id=service,name='Blood',category=request.POST['service_category'], valueunit='mg/dL')
            ObservationModel.objects.create(service_id=service,name='Specific Gravity',category=request.POST['service_category'], valueunit='Cel')
            ObservationModel.objects.create(service_id=service,name='Ketone',category=request.POST['service_category'], valueunit='mg/dL')
            ObservationModel.objects.create(service_id=service,name='Glucose',category=request.POST['service_category'], valueunit='Cel')
            service.save()
        elif request.POST['service'] == 'img1':        
            service.request_location = 'room4'     
            service.request_description = 'Chụp X-Quang'                   
            service.save()
        elif request.POST['service'] == 'img2':            
            service.request_location = 'room5'     
            service.request_description = 'Chụp MRI'                   
            service.save()
        elif request.POST['service'] == 'img3':
            service.request_location = 'room6'     
            service.request_description = 'Siêu âm'
            service.save()
        services = ServiceRequestModel.objects.all().filter(encounter_id = encounter_id)
        observations = ObservationModel.objects.all().filter(service_id = service.servicerequest_id)
        return render(request,'fhir/xetnghiem.html',{'group_name': group_name, 'user_name': user_name, 'data':data, 'services': services, 'observations': observations})    

class ketqua(View):
    def get(self,request, group_name, user_name, patient_identifier, encounter_id, service_id ):
        data = {'Patient':{'identifier': patient_identifier}, 'Encounter':{'id':encounter_id}}
        services = ServiceRequestModel.objects.all().filter(encounter_id = encounter_id)
        observations = ObservationModel.objects.all().filter(service_id = service_id)
        return render(request,'fhir/xetnghiem.html',{'group_name': group_name, 'user_name': user_name, 'data':data, 'services': services, 'observations': observations})    

    def post(self, request):
        pass

                

