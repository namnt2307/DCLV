import xml.etree.ElementTree as ET
import requests
import openpyxl as xl
from datetime import datetime
ns = {'d':"http://hl7.org/fhir"}

def identifier_type(resource, system, value, use="usual", _type=None, period=None, assigner=None):
    ET.SubElement(resource, 'use value=\"{}\"'.format(use))
    if _type:
        type_res = ET.SubElement(resource, 'type')
        codeable_concept(type_res, len(_type), _type)
    ET.SubElement(resource, 'system value=\"{}\"'.format(system))
    ET.SubElement(resource, 'value value=\"{:0>5}\"'.format(value))
    if period:
        period_res = ET.SubElement(resource, 'period')
        period_type(period_res, period)
    if assigner:
        assigner_res = ET.SubElement(resource, 'assigner')
        reference_type(assigner_res, assigner.reference,
                       assigner._type, assigner_res.identifier)

def period_type(resource, start=None, end=None):
    if start:
        ET.SubElement(resource, 'start value=\"{}\"'.format(start))
    if end:
        ET.SubElement(resource, 'end value=\"{}\"'.format(end))


def reference_type(resource, reference, _type, identifier=None, display=None):
    ET.SubElement(resource, 'reference value=\"{}\"'.format(reference))
    ET.SubElement(resource, 'type value=\"{}\"'.format(_type))
    if identifier:
        _identifier = ET.SubElement(resource, 'identifier')
        identifier_type(_identifier, identifier.get('system'), identifier.get('value'), identifier.get(
            'use'), identifier.get('type'), identifier.get('period'), identifier('assigner'))
    if display:
        ET.SubElement(resource, 'display value=\"{}\"'.format(display))


def name_type(resource, name, text=None, use=None):
    fam_name = name.split(' ')[0]
    given_name = ' '.join(name.split(' ')[1:])
    if not use:
        use = "official"
    ET.SubElement(resource, 'use value=\"{}\"'.format(use))
    if text:
        ET.SubElement(resource, 'text value=\"{}\"'.format(text))
    ET.SubElement(resource, 'family value=\"{}\"'.format(fam_name))
    ET.SubElement(resource, 'given value=\"{}\"'.format(given_name))


def address_type(resource, address, postalCode=None, country=None, use=None, type_=None):
    city = address.split(', ')[-1]
    district = address.split(', ')[-2]
    line = ' '.join(address.split(', ')[:-2])
    if not use:
        use = "home"
    if not type_:
        type_ = "both"
    if not postalCode:
        postalCode = "70000"
    if not country:
        country = "VietNam"
    ET.SubElement(resource, 'use value=\"{}\"'.format(use))
    ET.SubElement(resource, 'type value=\"{}\"'.format(type_))
    ET.SubElement(resource, 'line value=\"{}\"'.format(line))
    ET.SubElement(resource, 'city value=\"{}\"'.format(city))
    ET.SubElement(resource, 'district value=\"{}\"'.format(district))
    ET.SubElement(resource, 'postalCode value=\"{}\"'.format(postalCode))
    ET.SubElement(resource, 'country value=\"{}\"'.format(country))


def coding_type(resource, system, code, display=None, userSelected="false", version="4.0.1"):
    ET.SubElement(resource, 'system value=\"{}\"'.format(system))
    ET.SubElement(resource, 'version value=\"{}\"'.format(version))
    ET.SubElement(resource, 'code value=\"{}\"'.format(code))
    if display:
        ET.SubElement(resource, 'display value=\"{}\"'.format(display))
    ET.SubElement(resource, 'userSelected value=\"{}\"'.format(userSelected))


def contactpoint_type(resource, system, value, use=None, rank=None, period=None):
    ET.SubElement(resource, 'system value=\"{}\"'.format(system))
    ET.SubElement(resource, 'value value=\"{}\"'.format(value))
    if not use:
        use = "mobile"
    ET.SubElement(resource, 'use value=\"{}\"'.format(use))
    if rank:
        ET.SubElement(resource, 'rank value=\"{}\"'.format(rank))
    if period:
        period_type(resource, period)


def codeable_concept(resource, num_code=None, codes=None, text=None):
    if num_code and codes:
        for i in range(num_code):
            coding = ET.SubElement(resource, 'coding')
            coding_type(coding, codes[i].get('system'), codes[i].get(
                'code'), codes[i].get('display'), version=codes[i].get('version'))
    if text:
        ET.SubElement(resource, 'text value=\"{}\"'.format(text))


def quantity_type(resource, value, unit, system=None, code=None, comparator=None):
    ET.SubElement(resource, 'value value=\"{}\"'.format(value))
    if comparator:
        ET.SubElement(resource, 'comparator value=\"{}\"'.format(comparator))
    ET.SubElement(resource, 'unit value=\"{}\"'.format(unit))
    if system:
        ET.SubElement(resource, 'system value=\"{}\"'.format(system))
    if code:
        ET.SubElement(resource, 'code value=\"{}\"'.format(code))


def money_type(resource, value, currency):
    ET.SubElement(resource, 'value value=\"{}\"'.format(value))
    ET.SubElement(resource, 'currency value=\"{}\"'.format(currency))


def range_type(resource, low_limit, high_limit):
    low = ET.SubElement(resource, 'low')
    quantity_type(low, low_limit.value, low_limit.comparator,
                  low_limit.unit, low_limit.system, low_limit.code)
    high = ET.SubElement(resource, 'high')
    quantity_type(high, high_limit.value, high_limit.comparator,
                  high_limit.unit, high_limit.system, high_limit.code)


def ratio_type(resource, numerator_value, denominator_value):
    numerator = ET.SubElement(resource, 'numerator')
    quantity_type(numerator, numerator_value.value, numerator_value.comparator,
                  numerator_value.unit, numerator_value.system, numerator_value.code)
    denominator = ET.SubElement(resource, 'denominator')
    quantity_type(denominator, denominator_value.value, denominator_value.comparator,
                  denominator_value.unit, denominator_value.system, denominator_value.code)


def duration_type(resource, value, unit, system, code):
    ET.SubElement(resource, 'value value=\"{}\"'.format(value))
    ET.SubElement(resource, 'unit value=\"{}\"'.format(unit))
    ET.SubElement(resource, 'system value=\"{}\"'.format(system))
    ET.SubElement(resource, 'code value=\"{}\"'.format(code))


def get_observation(encounter_id):
    get_observation = requests.get("http://hapi.fhir.org/baseR4/Observation?encounter=" + str(encounter_id), headers={'Content-type': 'application/xml'})
    if get_observation.status_code == 200 and 'entry' in get_observation.content.decode('utf-8'):
        get_root = ET.fromstring(get_observation.content.decode('utf-8'))
        observation = []
        for entry in get_root.findall('d:entry', ns):
            resource = entry.find('d:resource', ns)
            observation_resource = resource.find('d:Observation', ns)
            code = observation_resource.find('d:code', ns)
            coding = code.find('d:coding', ns)
            display = coding.find('d:display', ns).attrib['value']
            quantity = observation_resource.find('d:valueQuantity', ns)
            value = quantity.find('d:value', ns).attrib['value'] + quantity.find('d:unit', ns).attrib['value'] 
            observation.append({'display': display, 'value': value})
        return observation
    else:
        return None

def getdatetime(datetime_str):
    get_datetime = datetime_str.split('+')[0]
    datetime_obj = datetime.strptime(get_datetime, '%Y-%m-%dT%H:%M:%S')
    return datetime.strftime(datetime_obj, "%H:%M:%S, %d-%m-%Y")


def get_encounter(encounter_id):
    encounter = {}
    get_encounter =  requests.get("http://hapi.fhir.org/baseR4/Encounter/" + str(encounter_id), headers={'Content-type': 'application/xml'})
    print(get_encounter.status_code)
    print(get_encounter.content)
    if get_encounter.status_code == 200:
        get_root = ET.fromstring(get_encounter.content.decode('utf-8'))
        encounter['id'] = get_root.find('d:id', ns).attrib['value']
        period = get_root.find('d:period', ns)
        encounter['start_date'] = period.find('d:start', ns).attrib['value']
        encounter['id'] = encounter_id
        return encounter
    else:
        return None


def get_patient_upload_data(excel_file):
    wb = xl.load_workbook(excel_file)
    sh = wb['Sheet1']
    m_row = sh.max_row
    last_line = 0
    data = {'Patient':{},'Encounter':{},'Observation':[]}
    for i in range(1,m_row+1):
        cell = sh.cell(row=i, column=4)
        if(cell.value):
            tag = sh.cell(row=i, column=2)
            if tag.value == 'HO_TEN':
                data['Patient']['name'] = cell.value
            elif tag.value =='MA_DKBD':
                data['Patient']['identifier'] = cell.value
            elif tag.value == 'NGAY_SINH':
                data['Patient']['birthDate'] = cell.value
            elif tag.value == 'GIOI_TINH':
                data['Patient']['gender'] = cell.value
            elif tag.value == 'DIA_CHI':
                data['Patient']['address'] = [{'address':cell.value}]
            elif tag.value == 'NGAY_VAO':
                data['Encounter']['period'] = {'start':cell.value}
                data['Encounter']['start_date'] = cell.value
            elif tag.value == 'NGAY_RA':
                if data['Encounter'].get('period'):
                    data['Encounter']['period']['stop'] = cell.value
                else:
                    data['Encounter']['period'] = {'stop':cell.value}
            elif tag.value == 'MA_LOAI_KCB':
                data['Encounter']['class'] = cell.value
            elif tag.value == 'MA_KHOA':
                data['Encounter']['location'] = cell.value
            elif tag.value == 'SO_NGAY_DTRI':
                data['Encounter']['length'] = cell.value                        
            elif not tag.value:
                tag_2 = sh.cell(row=i, column=3)
                tag_2_content = tag_2.value.split('.')
                if tag_2_content[0] == 'Patient':
                    if data['Patient'][tag_2_content[1]]:
                        data['Patient'][tag_2_content[1]].append({tag_2_content[1]:cell.value})
                        if len(tag_2_content) > 2:
                            for i in range(2, len(tag_2_content)):
                                data['Patient'][tag_2_content[1]][-1][tag_2_content[i].split('=')[0]] = tag_2_content[i].split('=')[1]
                elif tag_2_content[0] == 'Encounter':
                    if data['Encounter'][tag_2_content[1]]:
                        data['Encounter'][tag_2_content[1]].append({tag_2_content[1]:cell.value})
                        if len(tag_2_content) > 2:
                            for i in range(2, len(tag_2_content)):
                                data['Encounter'][tag_2_content[1]][-1][tag_2_content[i].split('=')[0]] = tag_2_content[i].split('=')[1]
                elif tag_2_content[0] == 'Observation':
                    _observation = {}
                    for i in range(1, len(tag_2_content)):
                        _observation[tag_2_content[i].split('=')[0]] = tag_2_content[i].split('=')[1]
                    _observation['valueQuantity'] = cell.value
                    data['Observation'].append(_observation)
    print(data)
    return data


def create_patient_resource(patient):
    root = ET.Element('Patient')
    tree = ET.ElementTree(root)
    root.set("xmlns","http://hl7.org/fhir")
    if patient.get('id'):
        id = ET.SubElement(root, 'id')
        id.set('value', patient['id'])
    if patient.get('identifier'):    
        identifier_resource = ET.SubElement(root, 'identifier')
        identifier_type(identifier_resource, 'urn:trinhcongminh', patient['identifier'], 'usual', [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'MR'}])
    if patient.get('name'):
        name = ET.SubElement(root, 'name')
        name_type(name, patient['name'])
    if patient.get('telecom'):
        telecom = ET.SubElement(root, 'telecom')
        contactpoint_type(telecom, 'phone', patient['telecom'])
    if patient.get('gender'):
        gender = ET.SubElement(root, 'gender')
        if patient['gender'] == 'Nam':
            code = 'male'
        elif patient['gender'] == 'Nữ':
            code = 'female'
        gender.set('value', code)
    if patient.get('birthDate'):
        birthDate = ET.SubElement(root, 'birthDate')
        birthDate.set('value', patient['birthDate'])
    if patient.get('home_address'):
        address = ET.SubElement(root,'address')
        address_type(address, patient['home_address'], use='home')
    if patient.get('work_address'):
        address = ET.SubElement(root,'address')
        address_type(address, patient['work_address'], use='work')
    if patient.get('contact'):
        contact = ET.SubElement(root, 'contact')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_encounter_resource(encounter, patient_id, patient_name):
    root = ET.Element('Encounter')
    tree = ET.ElementTree(root)
    root.set("xmlns","http://hl7.org/fhir")
    # identifier = ET.SubElement(root, 'identifier')
    # dttype.identifier_type(identifier, )
    if encounter.get('identifier'):
        identifier_resource = ET.SubElement(root, 'identifier')
        identifier_type(identifier_resource, 'urn:trinhcongminh', encounter['identifier'], 'usual', [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'MR'}])
    if not encounter.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', 'in-progress')
    else:
        status = ET.SubElement(root, 'status')
        status.set('value', encounter['status'])
    if encounter.get('class'):
        _class = ET.SubElement(root, 'class')
        coding_type(_class, 'http://terminology.hl7.org/CodeSystem/v3-ActCode', encounter['class'])
    if encounter.get('type'):
        _type = ET.SubElement(root, 'type')
        codeable_concept(_type,text=encounter['type'])
    if encounter.get('serviceType'):
        serviceType = ET.SubElement(root, 'serviceType')
        codeable_concept(serviceType,text=encounter['serviceType'])
    if encounter.get('priority'):
        priority = ET.SubElement(root, 'priority')
        codeable_concept(priority,1,[{'system':'http://terminology.hl7.org/ValueSet/v3-ActPriority','code':encounter['priority'], 'version':'2018-08-12'}])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/'+ patient_id, 'Patient', display=patient_name)
    if encounter.get('period'):
        period = ET.SubElement(root, 'period')
        period_type(period, encounter['period'].get('start'), encounter['period'].get('end'))
    if encounter.get('length'):
        length = ET.SubElement(root, 'length')
        duration_type(length, encounter['length'], 'days', 'http://unitsofmeasure.org', 'd')    
    # if data['Encounter'].get('location'):
    #     location = ET.SubElement(root, 'location')
    if encounter.get('serviceProvider'):
        serviceProvider = ET.SubElement(root, 'serviceProvider')
    return  ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)

def create_observation_resource(observation, patient_name, patient_id, encounter_id):
    root = ET.Element('Observation')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if observation.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', observation['status'])
    if observation.get('category'):
        category = ET.SubElement(root, 'category')
        coding = ET.SubElement(category, 'coding')
        coding_type(coding, 'http://terminology.hl7.org/CodeSystem/observation-category', observation['category'])
    if observation.get('code'):
        code = ET.SubElement(root, 'code')
        if patient_id:
            subject = ET.SubElement(root, 'subject')
            reference_type(subject, 'Patient/' + patient_id, 'Patient', display=patient_name)
        if encounter_id:
            encounter = ET.SubElement(root, 'encounter')
            reference_type(encounter, 'Encounter/'+encounter_id, 'Encounter')
        if observation['code'] == '8867-4':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8867-4', display='Heart rate')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'beats/minute', 'http://unitsofmeasure.org', '{Beats}/min')
        elif observation['code'] == '8310-5':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8867-4', display='Body temperature')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'Cel', 'http://unitsofmeasure.org', 'Cel')
        elif observation['code'] == '8480-6':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8480-6', display='Systolic blood pressure')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'mmHg', 'http://unitsofmeasure.org', 'mm[Hg]')
        elif observation['code'] == '8462-4':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8462-4', display='Diastolic blood pressure')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'mmHg', 'http://unitsofmeasure.org', 'mm[Hg]')
        elif observation['code'] == '9279-1':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '9279-1', display='Respiratory rate')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'breaths/minute', 'http://unitsofmeasure.org', '{Breaths}/min')
        elif observation['code'] == '29463-7':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '29463-7', display='Body weight')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'], 'kg', 'http://unitsofmeasure.org', 'kg')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)

def create_condition_resource(condition, patient_id, patient_name, encounter_id):
    root = ET.Element('Condition')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if condition.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh', condition['identifier'], 'usual')
    if condition.get('clinicalStatus'):
        clinical = ET.SubElement(root, 'clinicalStatus')
        codeable_concept(clinical, text=condition['clinicalStatus'])
    if condition.get('verificationStatus'):
        verify = ET.SubElement(root, 'verificationStatus')
        codeable_concept(verify, text=condition['verificationStatus'])
    if condition.get('category'):
        category = ET.SubElement(root, 'category')
        codeable_concept(category, text=condition['category'])
    if condition.get('severity'):
        severity = ET.SubElement(root, 'severity')
        codeable_concept(severity, text=condition['severity'])
    if condition.get('code'):
        code = ET.SubElement(root, 'code')
        codeable_concept(code, text=condition['code'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id, 'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/'+encounter_id, 'Encounter')            
    if condition.get('onset'):
        onset = ET.SubElement(root, 'onsetdateTime')
        onset.set('value', condition['onset'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_service_resource(service, patient_id, patient_name, encounter_id):
    root = ET.Element('ServiceRequest')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if service.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh', service['identifier'], 'usual')
    if service.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', service['status'])
    if service.get('intent'):
        intent = ET.SubElement(root, 'intent')
        intent.set('value', service['intent'])
    if service.get('category'):
        category = ET.SubElement(root, 'category')
        codeable_concept(category, text=service['category'])
    if service.get('code'):
        code = ET.SubElement(root, 'code')
        codeable_concept(code, text=service['code'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/'+ patient_id, 'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/'+ encounter_id, 'Patient')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)

def create_observation_resource(observation, patient_id, patient_name, encounter_id, service_id=None):
    root = ET.Element('Observation')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if observation.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh', observation['identifier'], 'usual')
    if service_id:
        basedOn = ET.SubElement(root, 'basedOn')
        reference_type(basedOn, 'ServiceRequest/' + service_id, 'ServiceRequest')
    if observation.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', observation['status'])
    if observation.get('category'):
        category = ET.SubElement(root, 'category')
        codeable_concept(category, text=observation['category'])
    if observation.get('code'):
        code = ET.SubElement(root, 'code')
        codeable_concept(code, text=observation['code'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id, 'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/' + encounter_id, 'Encounter')
    if observation.get('effective'):
        effectiveDateTime = ET.SubElement(root, 'effectiveDateTime')
        effectiveDateTime.set('value', observation['effective'])
    if observation.get('valuequantity'):
        valueQuantity = ET.SubElement(root, 'valueQuantity')
        quantity_type(valueQuantity, observation['valuequantity'], observation['valueunit'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def query_patient(patient_identifier):
    patient = {}
    get_req = requests.get("http://hapi.fhir.org/baseR4/Patient?identifier=urn:trinhcongminh|" + patient_identifier, headers={'Content-type': 'application/xml'})
    if get_req.status_code == 200 and 'entry' in get_req.content.decode('utf-8'):
        print(get_req.status_code)
        get_root = ET.fromstring(get_req.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        patient_resource = resource.find('d:Patient', ns)
        id_resource = patient_resource.find('d:id', ns)
        patient['id'] = id_resource.attrib['value']
        name_resource = patient_resource.find('d:name', ns)
        patient['name'] = name_resource.find('d:family', ns).attrib['value'] + ' ' + name_resource.find('d:given', ns).attrib['value']
        gender = patient_resource.find('d:gender', ns).attrib['value']
        telecom = patient_resource.find('d:telecom', ns)
        patient['telecom'] = telecom.find('d:value', ns).attrib['value']
        if gender == 'male':
            patient['gender'] = 'Nam'
        elif gender == 'female':
            patient['gender'] = 'Nữ'
        patient['birthDate'] = patient_resource.find('d:birthDate', ns).attrib['value']
        patient['address'] = []
        for address in patient_resource.findall('d:address', ns):
            addr_type = address.find('d:use', ns).attrib['value']
            if addr_type == 'home':
                patient['home_address'] = address.find('d:line', ns).attrib['value'] + ', ' + address.find('d:district', ns).attrib['value'] + ', ' + address.find('d:city', ns).attrib['value']
            elif addr_type == 'work':
                patient['work_address'] = address.find('d:line', ns).attrib['value'] + ', ' + address.find('d:district', ns).attrib['value'] + ', ' + address.find('d:city', ns).attrib['value']
        patient['identifier'] = patient_identifier
        return patient
    else:
        return None

def query_encounter(encounter_identifier):
    encounter = {}
    encounter['identifier'] = encounter_identifier
    get_encounter = requests.get("http://hapi.fhir.org/baseR4/Encounter?identifier=urn:trinhcongminh|" + encounter_identifier, headers={'Content-type': 'application/xml'})
    if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
        get_root = ET.fromstring(get_encounter.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        encounter_resource = resource.find('d:Encounter', ns)
        encounter['id'] = encounter_resource.find('d:id', ns).attrib['value']
        encounter['status'] = encounter_resource.find('d:status', ns).attrib['value']
        _class = encounter_resource.find('d:class', ns)
        encounter['class'] = _class.find('d:code', ns).attrib['value']
        _type = encounter_resource.find('d:type', ns)
        encounter['type'] = _type.find('d:text', ns).attrib['value']
        servicetype = encounter_resource.find('d:serviceType', ns)
        encounter['serviceType'] = servicetype.find('d:text', ns).attrib['value']
        priority = encounter_resource.find('d:priority', ns)
        encounter['priority'] = priority.find('d:text', ns)
        period = encounter_resource.find('d:period', ns)
        encounter['start'] = period.find('d:start', ns).attrib['value']
        end_date = None
        if period.find('d:end', ns) != None:
            end_date = period.find('d:end', ns).attrib['value']
            encounter['end'] = getdatetime(end_date)
    print(encounter)
    return encounter
        


def query_service(service_identifier):
    service = {}
    service['identifier'] = service_identifier
    get_encounter = requests.get("http://hapi.fhir.org/baseR4/ServiceRequest?identifier=urn:trinhcongminh|" + service_identifier, headers={'Content-type': 'application/xml'})
    if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
        get_root = ET.fromstring(get_encounter.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        service_resource = resource.find('d:ServiceRequest', ns)
        service['id'] = service_resource.find('d:id', ns).attrib['value']
        service['status'] = service_resource.find('d:status', ns).attrib['value']
        category = service_resource.find('d:category', ns)
        service['category'] = category.find('d:text', ns).attrib['value']
        code = service_resource.find('d:code', ns)
        service['code'] = code.find('d:text', ns)
    print(service)
    return service