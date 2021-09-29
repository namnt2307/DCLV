from fhir.models import EncounterModel
import xml.etree.ElementTree as ET
import requests
import openpyxl as xl
from datetime import datetime
ns = {'d': "http://hl7.org/fhir"}

fhir_server = "http://10.0.0.16:8080/fhir"

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


def annotation_type(resource, text, author=None, time=None):
    if author:
        ET.SubElement(resource, 'author')
    if time:
        ET.SubElement(resource, 'time')
        time.set('value', time)
    textobject = ET.SubElement(resource, 'text')
    textobject.set('value', text)


def timing_type(resource, duration_value, frequency_value, period_value, when_value, offset_value=None, event_value=None):
    if event_value:
        event = ET.SubElement(resource, 'event')
        event.set('value', event_value)
    repeat = ET.SubElement(resource, 'repeat')
    get_duration = duration_value.split(' ')
    duration = ET.SubElement(repeat, 'duration')
    if '-' in get_duration[0]:
        duration.set('value', get_duration[0].split('-')[0])
        durationMax = ET.SubElement(repeat, 'durationMax')
        durationMax.set('value', get_duration[0].split('-')[1])
    else:
        duration.set('value', get_duration[0])
    durationUnit = ET.SubElement(repeat, 'durationUnit')
    durationUnit.set('value', get_duration[1])
    get_frequency = frequency_value.split(' ')
    frequency = ET.SubElement(repeat, 'frequency')
    if '-' in get_frequency[0]:
        frequency.set('value', get_frequency[0].split('-')[0])
        frequencyMax = ET.SubElement(repeat, 'frequencyMax')
        frequencyMax.set('value', get_frequency[0].split('-')[1])
    else:
        frequency.set('value', get_frequency[0])
    get_period = period_value.split(' ')
    period = ET.SubElement(repeat, 'period')
    if '-' in get_period[0]:
        period.set('value', get_period[0].split('-')[0])
        periodMax = ET.SubElement(repeat, 'periodMax')
        periodMax.set('value', get_period[0].split('-')[1])
    else:
        period.set('value', get_period[0])
    periodUnit = ET.SubElement(repeat, 'periodUnit')
    periodUnit.set('value', get_period[1])
    when = ET.SubElement(repeat, 'when')
    when.set('value', when_value)
    if offset_value:
        offset = ET.SubElement(repeat, 'offset')
        offset.set('value', offset_value)


def get_observation(encounter_id):
    get_observation = requests.get(fhir_server + "/Observation?encounter=" + str(
        encounter_id), headers={'Content-type': 'application/xml'})
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
            value = quantity.find(
                'd:value', ns).attrib['value'] + quantity.find('d:unit', ns).attrib['value']
            observation.append({'display': display, 'value': value})
        return observation
    else:
        return None


def getdatetime(datetime_str):
    get_datetime = datetime_str.split('+')[0]
    datetime_obj = datetime.strptime(get_datetime, '%Y-%m-%dT%H:%M:%S')
    return datetime.strftime(datetime_obj, "%Y-%m-%d %H:%M:%S")


def get_encounter(encounter_id):
    encounter = {}
    get_encounter = requests.get(fhir_server + "/Encounter/" + str(
        encounter_id), headers={'Content-type': 'application/xml'})
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
    data = {'Patient': {}, 'Encounter': {}, 'Observation': []}
    for i in range(1, m_row+1):
        cell = sh.cell(row=i, column=4)
        if(cell.value):
            tag = sh.cell(row=i, column=2)
            if tag.value == 'HO_TEN':
                data['Patient']['name'] = cell.value
            elif tag.value == 'MA_DKBD':
                data['Patient']['identifier'] = cell.value
            elif tag.value == 'NGAY_SINH':
                data['Patient']['birthDate'] = cell.value
            elif tag.value == 'GIOI_TINH':
                data['Patient']['gender'] = cell.value
            elif tag.value == 'DIA_CHI':
                data['Patient']['address'] = [{'address': cell.value}]
            elif tag.value == 'NGAY_VAO':
                data['Encounter']['period'] = {'start': cell.value}
                data['Encounter']['start_date'] = cell.value
            elif tag.value == 'NGAY_RA':
                if data['Encounter'].get('period'):
                    data['Encounter']['period']['stop'] = cell.value
                else:
                    data['Encounter']['period'] = {'stop': cell.value}
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
                        data['Patient'][tag_2_content[1]].append(
                            {tag_2_content[1]: cell.value})
                        if len(tag_2_content) > 2:
                            for i in range(2, len(tag_2_content)):
                                data['Patient'][tag_2_content[1]][-1][tag_2_content[i].split(
                                    '=')[0]] = tag_2_content[i].split('=')[1]
                elif tag_2_content[0] == 'Encounter':
                    if data['Encounter'][tag_2_content[1]]:
                        data['Encounter'][tag_2_content[1]].append(
                            {tag_2_content[1]: cell.value})
                        if len(tag_2_content) > 2:
                            for i in range(2, len(tag_2_content)):
                                data['Encounter'][tag_2_content[1]][-1][tag_2_content[i].split(
                                    '=')[0]] = tag_2_content[i].split('=')[1]
                elif tag_2_content[0] == 'Observation':
                    _observation = {}
                    for i in range(1, len(tag_2_content)):
                        _observation[tag_2_content[i].split(
                            '=')[0]] = tag_2_content[i].split('=')[1]
                    _observation['valueQuantity'] = cell.value
                    data['Observation'].append(_observation)
    print(data)
    return data


def create_patient_resource(patient):
    root = ET.Element('Patient')
    tree = ET.ElementTree(root)
    root.set("xmlns", "http://hl7.org/fhir")
    if patient.get('id'):
        id = ET.SubElement(root, 'id')
        id.set('value', patient['id'])
    if patient.get('identifier'):
        identifier_resource = ET.SubElement(root, 'identifier')
        identifier_type(identifier_resource, 'urn:trinhcongminh', patient['identifier'], 'usual', [
                        {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'MR'}])
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
    if patient.get('birthdate'):
        birthDate = ET.SubElement(root, 'birthDate')
        birthDate.set('value', patient['birthdate'])
    if patient.get('home_address'):
        address = ET.SubElement(root, 'address')
        address_type(address, patient['home_address'], use='home')
    if patient.get('work_address'):
        address = ET.SubElement(root, 'address')
        address_type(address, patient['work_address'], use='work')
    if patient.get('contact'):
        contact = ET.SubElement(root, 'contact')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_encounter_resource(encounter, patient_id, patient_name, practitioner_id):
    root = ET.Element('Encounter')
    tree = ET.ElementTree(root)
    root.set("xmlns", "http://hl7.org/fhir")
    # identifier = ET.SubElement(root, 'identifier')
    # dttype.identifier_type(identifier, )
    if encounter.get('id'):
        id_ = ET.SubElement(root, 'id')
        id_.set('value', encounter['id'])
    if encounter.get('identifier'):
        identifier_resource = ET.SubElement(root, 'identifier')
        identifier_type(identifier_resource, 'urn:trinhcongminh', encounter['identifier'], 'usual', [
                        {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'MR'}])
    if not encounter.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', 'in-progress')
    else:
        status = ET.SubElement(root, 'status')
        status.set('value', encounter['status'])
    if encounter.get('class'):
        _class = ET.SubElement(root, 'class')
        coding_type(
            _class, 'http://terminology.hl7.org/CodeSystem/v3-ActCode', encounter['class'])
    if encounter.get('type'):
        _type = ET.SubElement(root, 'type')
        codeable_concept(_type, text=encounter['type'])
    if encounter.get('serviceType'):
        serviceType = ET.SubElement(root, 'serviceType')
        codeable_concept(serviceType, text=encounter['serviceType'])
    if encounter.get('priority'):
        priority = ET.SubElement(root, 'priority')
        codeable_concept(priority, 1, [
                         {'system': 'http://terminology.hl7.org/CodeSystem/v3-ActPriority', 'code': encounter['priority'], 'version':'2018-08-12'}])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    participant = ET.SubElement(root, 'participant')
    reference_type(participant, 'Practitioner/' +
                   practitioner_id, 'Practitioner')
    if encounter.get('period'):
        period = ET.SubElement(root, 'period')
        period_type(period, encounter['period'].get(
            'start'), encounter['period'].get('end'))
    if encounter.get('length'):
        length = ET.SubElement(root, 'length')
        duration_type(length, encounter['length'],
                      'days', 'http://unitsofmeasure.org', 'd')
    if encounter.get('reasonCode'):
        reason = ET.SubElement(root, 'reasonCode')
        codeable_concept(reason, text=encounter['reasonCode'])
    if encounter.get('conditions'):
        for condition in encounter['conditions']:
            diagnosis = ET.SubElement(root, 'diagnosis')
            condition_ref = ET.SubElement(diagnosis, 'condition')
            reference_type(condition_ref, 'Condition/' +
                           condition['id'], 'Condition')
            condition_use = ET.SubElement(diagnosis, 'use')
            code = None
            if condition['use'] == 'admission':
                code = {'system': 'http://terminology.hl7.org/CodeSystem/diagnosis-role',
                        'code': 'AD', 'display': 'admission diagnosis'}
            elif condition['use'] == 'discharge':
                code = {'system': 'http://terminology.hl7.org/CodeSystem/diagnosis-role',
                        'code': 'DD', 'display': 'discharge diagnosis'}
            codeable_concept(condition_use, 1, [code])
    # if data['Encounter'].get('location'):
    #     location = ET.SubElement(root, 'location')
    if encounter.get('serviceProvider'):
        serviceProvider = ET.SubElement(root, 'serviceProvider')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


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
        coding_type(
            coding, 'http://terminology.hl7.org/CodeSystem/observation-category', observation['category'])
    if observation.get('code'):
        code = ET.SubElement(root, 'code')
        if patient_id:
            subject = ET.SubElement(root, 'subject')
            reference_type(subject, 'Patient/' + patient_id,
                           'Patient', display=patient_name)
        if encounter_id:
            encounter = ET.SubElement(root, 'encounter')
            reference_type(encounter, 'Encounter/'+encounter_id, 'Encounter')
        if observation['code'] == '8867-4':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org',
                        '8867-4', display='Heart rate')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'],
                          'beats/minute', 'http://unitsofmeasure.org', '{Beats}/min')
        elif observation['code'] == '8310-5':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org',
                        '8867-4', display='Body temperature')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(
                valueQuantity, observation['valueQuantity'], 'Cel', 'http://unitsofmeasure.org', 'Cel')
        elif observation['code'] == '8480-6':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8480-6',
                        display='Systolic blood pressure')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(
                valueQuantity, observation['valueQuantity'], 'mmHg', 'http://unitsofmeasure.org', 'mm[Hg]')
        elif observation['code'] == '8462-4':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org', '8462-4',
                        display='Diastolic blood pressure')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(
                valueQuantity, observation['valueQuantity'], 'mmHg', 'http://unitsofmeasure.org', 'mm[Hg]')
        elif observation['code'] == '9279-1':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org',
                        '9279-1', display='Respiratory rate')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(valueQuantity, observation['valueQuantity'],
                          'breaths/minute', 'http://unitsofmeasure.org', '{Breaths}/min')
        elif observation['code'] == '29463-7':
            coding = ET.SubElement(code, 'coding')
            coding_type(coding, 'http://loinc.org',
                        '29463-7', display='Body weight')
            valueQuantity = ET.SubElement(root, 'valueQuantity')
            quantity_type(
                valueQuantity, observation['valueQuantity'], 'kg', 'http://unitsofmeasure.org', 'kg')
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_condition_resource(condition, patient_id, patient_name, encounter_id):
    root = ET.Element('Condition')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if condition.get('id'):
        id_ = ET.SubElement(root, 'id')
        id_.set('value', condition['id'])
    if condition.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        condition['identifier'], 'usual')
    if condition.get('clinicalStatus'):
        clinical = ET.SubElement(root, 'clinicalStatus')
        codeable_concept(clinical, 1, [{'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                         'code': condition['clinicalStatus'], 'version':'2018-08-12'}], text=condition['clinicalStatus'])
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
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/'+encounter_id, 'Encounter')
    if condition.get('onset'):
        onset = ET.SubElement(root, 'onsetDateTime')
        onset.set('value', condition['onset'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_service_resource(service, patient_id, patient_name, encounter_id):
    root = ET.Element('ServiceRequest')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if service.get('id'):
        id_ = ET.SubElement(root, 'id')
        id_.set('value', service['id'])
    if service.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        service['identifier'], 'usual')
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
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/' + encounter_id, 'Encounter')
    if service.get('occurrence'):
        occurrence = ET.SubElement(root, 'occurrenceDateTime')
        occurrence.set('value', service['occurrence'])
    if service.get('authoredOn'):
        authoredOn = ET.SubElement(root, 'authoredOn')
        authoredOn.set('value', service['authoredOn'])
    if service.get('requester'):
        requester = ET.SubElement(root, 'requester')
        reference_type(requester, 'Practitioner/' + service['requester'], 'Practitioner')
    if service.get('note'):
        note = ET.SubElement(root, 'note')
        annotation_type(note, text=service['note'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_observation_resource(observation, patient_id, patient_name, encounter_id, service_id=None):
    root = ET.Element('Observation')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if observation.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        observation['identifier'], 'usual')
    if service_id:
        basedOn = ET.SubElement(root, 'basedOn')
        reference_type(basedOn, 'ServiceRequest/' +
                       service_id, 'ServiceRequest')
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
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/' + encounter_id, 'Encounter')
    if observation.get('effective'):
        effectiveDateTime = ET.SubElement(root, 'effectiveDateTime')
        effectiveDateTime.set('value', observation['effective'])
    if observation.get('performer'):
        performer = ET.SubElement(root, 'performer')
        reference_type(performer, 'Practitioner/' + observation['performer'], 'Practitioner')
    if observation.get('valuequantity'):
        valueQuantity = ET.SubElement(root, 'valueQuantity')
        quantity_type(
            valueQuantity, observation['valuequantity'], observation['valueunit'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_procedure_resource(procedure, patient_id, patient_name, encounter_id,  service_id):
    root = ET.Element('Procedure')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if procedure.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        procedure['identifier'], 'usual')
    if service_id:
        basedOn = ET.SubElement(root, 'basedOn')
        reference_type(basedOn, 'ServiceRequest/' +
                       service_id, 'ServiceRequest')
    if procedure.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', procedure['status'])
    if procedure.get('category'):
        category = ET.SubElement(root, 'category')
        codeable_concept(category, text=procedure['category'])
    if procedure.get('code'):
        code = ET.SubElement(root, 'code')
        codeable_concept(code, text=procedure['code'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/' + encounter_id, 'Encounter')
    if procedure.get('performedDateTime'):
        performeddateTime = ET.SubElement(root, 'performedDateTime')
        performeddateTime.set('value', procedure['performedDateTime'])
        print(procedure['performedDateTime'])
    if procedure.get('asserter'):
        asserter = ET.SubElement(root, 'asserter')
        reference_type(asserter, 'Practitioner/' +
                       procedure['asserter'], 'Practitioner')
    if procedure.get('performer'):
        performer = ET.SubElement(root, 'performer')
        reference_type(performer, 'Practitioner/' +
                       procedure['performer'], 'Practitioner')
    if procedure.get('reasonCode'):
        reasonCode = ET.SubElement(root, 'reasonCode')
        codeable_concept(reasonCode, text=procedure['reasonCode'])
    if procedure.get('outcome'):
        outcome = ET.SubElement(root, 'outcome')
        codeable_concept(outcome, text=procedure['outcome'])
    if procedure.get('complication'):
        complication = ET.SubElement(root, 'complication')
        codeable_concept(complication, text=procedure['complication'])
    if procedure.get('followUp'):
        followUp = ET.SubElement(root, 'followUp')
        codeable_concept(followUp, text=procedure['followUp'])
    if procedure.get('note'):
        note = ET.SubElement(root, 'note')
        annotation_type(note, text=procedure['note'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_medication_resource(medication, patient_id, patient_name, encounter_id):
    root = ET.Element('MedicationStatement')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if medication.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        medication['identifier'], 'usual')
    if medication.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', medication['status'])
    if medication.get('medication'):
        medicationobject = ET.SubElement(root, 'medicationCodeableConcept')
        codeable_concept(medicationobject, text=medication['medication'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id,
                   'Patient', display=patient_name)
    context = ET.SubElement(root, 'context')
    reference_type(context, 'Encounter/' + encounter_id, 'Encounter')
    if medication.get('effective'):
        effective = ET.SubElement(root, 'effectiveDateTime')
        effective.set('value', medication['effective'])
        print(medication['effective'])
    if medication.get('dateAsserted'):
        dateAsserted = ET.SubElement(root, 'dateAsserted')
        dateAsserted.set('value', medication['dateAsserted'])
        print(medication['dateAsserted'])
    if medication.get('reasonCode'):
        reasonCode = ET.SubElement(root, 'reasonCode')
        codeable_concept(reasonCode, text=medication['reasonCode'])
    dosage = ET.SubElement(root, 'dosage')
    if medication.get('additionalInstruction'):
        additionalInstruction = ET.SubElement(dosage, 'additionalInstruction')
        codeable_concept(additionalInstruction,
                         text=medication['additionalInstruction'])
    if medication.get('patientInstruction'):
        patientInstruction = ET.SubElement(dosage, 'patientInstruction')
        patientInstruction.set('value', medication['patientInstruction'])
    timing = ET.SubElement(dosage, 'timing')
    if medication.get('frequency') and medication.get('period') and medication.get('duration') and medication.get('when'):
        timing_type(timing, medication['duration'], medication['frequency'],
                    medication['period'], medication['when'], medication.get('offset'))
    if medication.get('route'):
        route = ET.SubElement(dosage, 'route')
        codeable_concept(route, text=medication['route'])
    if medication.get('quantity'):
        doseAndRate = ET.SubElement(dosage, 'doseAndRate')
        doseQuantity = ET.SubElement(doseAndRate, 'doseQuantity')
        dose_value = medication['quantity'].split(' ')[0]
        dose_unit = medication['quantity'].split(' ')[1]
        quantity_type(doseQuantity, dose_value, dose_unit)
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def create_diagnostic_report_resource(diagnostic_report, patient_id, patient_name, encounter_id, service_id):
    root = ET.Element('DiagnosticReport')
    tree = ET.ElementTree(root)
    root.set('xmlns', 'http://hl7.org/fhir')
    if diagnostic_report.get('id'):
        id_ = ET.SubElement(root, 'id')
        id_.set('value', diagnostic_report['id'])
    if diagnostic_report.get('identifier'):
        identifier = ET.SubElement(root, 'identifier')
        identifier_type(identifier, 'urn:trinhcongminh',
                        diagnostic_report['identifier'], 'usual' )
    based_on = ET.SubElement(root, 'basedOn')
    reference_type(based_on, 'ServiceRequest/' + service_id, 'ServiceRequest')
    if diagnostic_report.get('status'):
        status = ET.SubElement(root, 'status')
        status.set('value', diagnostic_report['status'])
    if diagnostic_report.get('category'):
        category = ET.SubElement(root, 'category')
        codeable_concept(category, text=diagnostic_report['category'])
    if diagnostic_report.get('code'):
        code = ET.SubElement(root, 'code')
        codeable_concept(code, text=diagnostic_report['code'])
    subject = ET.SubElement(root, 'subject')
    reference_type(subject, 'Patient/' + patient_id, 'Patient', display=patient_name)
    encounter = ET.SubElement(root, 'encounter')
    reference_type(encounter, 'Encounter/' + encounter_id, 'Encounter')
    if diagnostic_report.get('effective'):
        effective_datetime = ET.SubElement(root, 'effectiveDateTime')
        effective_datetime.set('value', diagnostic_report['effective'])
    if diagnostic_report.get('performer'):
        performer = ET.SubElement(root, 'performer')
        reference_type(performer, 'Practitioner/' + diagnostic_report['performer'], 'Practitioner')
    if diagnostic_report.get('conclusion'):
        conclusion = ET.SubElement(root, 'conclusion')
        conclusion.set('value', diagnostic_report['conclusion'])
    return ET.tostring(root, encoding="us-ascii", method="xml", xml_declaration=None, default_namespace=None, short_empty_elements=True)


def query_patient(patient_identifier,get_id):
    patient = {}
    get_req = requests.get(fhir_server + "/Patient?identifier=urn:trinhcongminh|" +
                           patient_identifier, headers={'Content-type': 'application/xml'})
    if get_req.status_code == 200 and 'entry' in get_req.content.decode('utf-8'):
        get_root = ET.fromstring(get_req.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        patient_resource = resource.find('d:Patient', ns)
        if get_id == True:
            id_resource = patient_resource.find('d:id', ns)
            patient['id'] = id_resource.attrib['value']
        name = patient_resource.find('d:name', ns)
        if name:
            patient['name'] = name.find(
                'd:family', ns).attrib['value'] + ' ' + name.find('d:given', ns).attrib['value']
        telecom = patient_resource.find('d:telecom', ns)
        if telecom:
            patient['telecom'] = telecom.find('d:value', ns).attrib['value']
        gender = patient_resource.find('d:gender', ns)
        if gender:
            if gender.attrib['value'] == 'male':
                patient['gender'] = 'Nam'
            elif gender.attrib['value'] == 'female':
                patient['gender'] = 'Nữ'
        birthdate = patient_resource.find('d:birthDate', ns)
        if birthdate:
            patient['birthdate'] = birthdate.attrib['value']
        for address in patient_resource.findall('d:address', ns):
            addr_type = address.find('d:use', ns).attrib['value']
            if addr_type == 'home':
                patient['home_address'] = address.find('d:line', ns).attrib['value'] + ', ' + address.find(
                    'd:district', ns).attrib['value'] + ', ' + address.find('d:city', ns).attrib['value']
            elif addr_type == 'work':
                patient['work_address'] = address.find('d:line', ns).attrib['value'] + ', ' + address.find(
                    'd:district', ns).attrib['value'] + ', ' + address.find('d:city', ns).attrib['value']
        patient['identifier'] = patient_identifier
        return patient
    else:
        return None


def query_encounter(encounter_identifier, get_id):
    encounter = {}
    get_encounter = requests.get(fhir_server + "/Encounter?identifier=urn:trinhcongminh|" +
                                 encounter_identifier, headers={'Content-type': 'application/xml'})
    if get_encounter.status_code == 200 and 'entry' in get_encounter.content.decode('utf-8'):
        get_root = ET.fromstring(get_encounter.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        encounter_resource = resource.find('d:Encounter', ns)
        if get_id == True:
            encounter['id'] = encounter_resource.find('d:id', ns).attrib['value']
        encounter['encounter_identifier'] = encounter_identifier
        status = encounter_resource.find('d:status', ns)
        if status:
            encounter['encounter_status'] = status.attrib['value']
        _class = encounter_resource.find('d:class', ns)
        if _class:
            encounter['encounter_class'] = _class.find('d:code', ns).attrib['value']
        _type = encounter_resource.find('d:type', ns)
        if _type:
            encounter['encounter_type'] = _type.find('d:text', ns).attrib['value']
        service_type = encounter_resource.find('d:serviceType', ns)
        if service_type:
            encounter['encounter_service'] = service_type.find(
                'd:text', ns).attrib['value']
        priority = encounter_resource.find('d:priority', ns)
        if priority:
            priority_coding = priority.find('d:coding', ns)
            encounter['encounter_priority'] = priority_coding.find(
                'd:value', ns)
        period = encounter_resource.find('d:period', ns)
        if period:
            encounter['encounter_start'] = period.find('d:start', ns).attrib['value']
            end_date = None
            if period.find('d:end', ns) != None:
                end_date = period.find('d:end', ns).attrib['value']
                encounter['encounter_end'] = getdatetime(end_date)
        reason_code = encounter_resource.find('d:reasonCode', ns)
        if reason_code:
            encounter['encounter_reason'] = reason_code.find('d:text', ns).attrib['value']
    return encounter


def query_service(service_identifier, get_id):
    service = {}
    get_service = requests.get(fhir_server + "/ServiceRequest?identifier=urn:trinhcongminh|" +
                               service_identifier, headers={'Content-type': 'application/xml'})
    if get_service.status_code == 200 and 'entry' in get_service.content.decode('utf-8'):
        get_root = ET.fromstring(get_service.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        service_resource = resource.find('d:ServiceRequest', ns)
        if get_id == True:
            service['id'] = service_resource.find('d:id', ns).attrib['value']
        service['service_identifier'] = service_identifier
        status = service_resource.find('d:status', ns)
        if status:
            service['service_status'] = status.attrib['value']
        category = service_resource.find('d:category', ns)
        if category:
            service['service_category'] = category.find(
                'd:text', ns).attrib['value']
        code = service_resource.find('d:code', ns)
        if code:
            service['service_code'] = code.find('d:text', ns).attrib['value']
        occurrence = service_resource.find('d:occurrenceDateTime', ns)
        if occurrence:
            service['service_occurrence'] = occurrence.attrib['value']
        authored_on = service_resource.find('d:authoredOn', ns)
        if authored_on:
            service['service_authored'] = authored_on.attrib['value']
        note = service_resource.find('d:note', ns)
        if note:
            service['service_note'] = note.find('d:text', ns).attrib['value']
    return service


def query_condition(condition_identifier, get_id):
    condition = {}
    get_condition = requests.get(fhir_server + "/Condition?identifier=urn:trinhcongminh|" +
                                 condition_identifier, headers={'Content-type': 'application/xml'})
    if get_condition.status_code == 200 and 'entry' in get_condition.content.decode('utf-8'):
        get_root = ET.fromstring(get_condition.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        condition_resource = resource.find('d:Condition', ns)
        if get_id == True:
            condition['id'] = condition_resource.find('d:id', ns).attrib['value']
        condition['condition_identifier'] = condition_identifier
        clinical_status = condition_resource.find('d:clinicalStatus', ns)
        if clinical_status:
            condition['condition_clinical_status'] = clinical_status.find(
                'd:text', ns).attrib['value']
        severity = condition_resource.find('d:severity', ns)
        if severity:
            condition['condition_severiy'] = severity.find(
                'd:text', ns).attrib['value']
        code = condition_resource.find('d:code', ns)
        if code:
            condition['condition_code'] = code.find('d:text', ns).attrib['value']
        onset = condition_resource.find('d:onsetDateTime', ns)
        if onset:
            condition['condition_onset'] = getdatetime(onset.attrib['value'])
    return(condition)


def query_observation(observation_identifier, get_id):
    observation = {}
    get_observation = requests.get(fhir_server + "/Observation?identifier=urn:trinhcongminh|" +
                                   observation_identifier, headers={'Content-type': 'application/xml'})
    if get_observation.status_code == 200 and 'entry' in get_observation.content.decode('utf-8'):
        get_root = ET.fromstring(get_observation.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        observation_resource = resource.find('d:Observation', ns)
        if get_id == True:
            observation['id'] = observation_resource.find(
                'd:id', ns).attrib['value']
        observation['observation_identifier'] = observation_identifier
        status = observation_resource.find('d:status', ns)
        if status:
            observation['observation_status'] = status.attrib['value']
        category = observation_resource.find('d:category', ns)
        if category:
            observation['observation_category'] = category.find(
                'd:text', ns).attrib['value']
        code = observation_resource.find('d:code', ns)
        if code:
            observation['observation_code'] = code.find(
                'd:text', ns).attrib['value']
        effective = observation_resource.find('d:effectiveDateTime', ns)
        if effective:
            observation['observation_effective'] = getdatetime(effective.attrib['value'])
        value_quantity = observation_resource.find('d:valueQuantity', ns)
        if value_quantity:
            observation['observation_value_quantity'] = value_quantity.find(
                'd:value', ns).attrib['value']
            observation['observation_value_unit'] = value_quantity.find(
                'd:unit', ns).attrib['value']
    return observation


def query_procedure(procedure_identifier, get_id):
    procedure = {}
    get_procedure = requests.get(fhir_server + "/Procedure?identifier=urn:trinhcongminh|" +
                                 procedure_identifier, headers={'Content-type': 'application/xml'})
    if get_procedure.status_code == 200 and 'entry' in get_procedure.content.decode('utf-8'):
        get_root = ET.fromstring(get_procedure.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        procedure_resource = resource.find('d:Procedure', ns)
        if get_id:
            procedure['id'] = procedure_resource.find('d:id', ns).attrib['value']
        procedure['procedure_identifier'] = procedure_identifier
        status = procedure_resource.find('d:status', ns)
        if status:
            procedure['procedure_status'] = status.attrib['value']
        category = procedure_resource.find('d:category', ns)
        if category:
            procedure['procedure_category'] = category.find(
                'd:text', ns).attrib['value']
        code = procedure_resource.find('d:code', ns)
        if code:
            procedure['procedure_code'] = code.find('d:text', ns).attrib['value']
        performed_datetime = procedure_resource.find('d:performedDateTime', ns)
        if performed_datetime:
            procedure['procedure_performed_datetime'] = getdatetime(performed_datetime.attrib['value'])
        reason_code = procedure_resource.find('d:reasonCode', ns)
        if reason_code:
            procedure['procedure_reason_code'] = reason_code.find(
                'd:text', ns).attrib['value']
        outcome = procedure_resource.find('d:outcome', ns)
        if outcome:
            procedure['procedure_outcome'] = outcome.find(
                'd:text', ns).attrib['value']
        complication = procedure_resource.find('d:complication', ns)
        if complication:
            procedure['procedure_complication'] = complication.find(
                'd:text', ns).attrib['value']
        follow_up = procedure_resource.find('d:followUp', ns)
        if follow_up:
            procedure['procedure_follow_up'] = follow_up.find(
                'd:text', ns).attrib['value']
        note = procedure_resource.find('d:note', ns)
        if note:
            procedure['procedure_note'] = note.find('d:text', ns).attrib['value']
    return procedure


def query_medication(medication_identifier, get_id):
    medication_statement = {}
    get_medication = requests.get(fhir_server + "/MedicationStatement?identifier=urn:trinhcongminh|" +
                                  medication_identifier, headers={'Content-type': 'application/xml'})
    if get_medication.status_code == 200 and 'entry' in get_medication.content.decode('utf-8'):
        get_root = ET.fromstring(get_medication.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        medication_resource = resource.find('d:MedicationStatement', ns)
        if get_id == True:
            medication_statement['id'] = medication_resource.find(
                'd:id', ns).attrib['value']
        medication_statement['medication_identifier'] = medication_identifier
        medication = medication_resource.find(
            'd:medicationCodeableConcept', ns)
        if medication:
            medication_statement['medication_medication'] = medication.find(
                'd:text', ns).attrib['value']
        effective = medication_resource.find('d:effectiveDateTime', ns)
        if effective:
            medication_statement['medication_effective'] = effective.attrib['value']
        date_asserted = medication_resource.find('d:dateAsserted', ns)
        if date_asserted:
            medication_statement['medication_date_asserted'] = date_asserted.attrib['value']
        reason_code = medication_resource.find('d:reasonCode', ns)
        if reason_code:
            medication_statement['medication_reason_code'] = reason_code.find(
                'd:text', ns).attrib['value']
        dosage = medication_resource.find('d:dosage', ns)
        if dosage:
            additional_instruction = dosage.find('d:additionalInstruction', ns)
            if additional_instruction:
                medication_statement['dosage_additional_instruction'] = additional_instruction.find(
                    'd:text', ns).attrib['value']
            patient_instruction = dosage.find('d:patientInstruction', ns)
            if patient_instruction:
                medication_statement['dosage_patient_instruction'] = patient_instruction.find(
                    'd:text', ns).attrib['value']
            timing = dosage.find('d:timing', ns)
            if timing:
                repeat = timing.find('d:repeat', ns)
                if repeat:
                    duration = repeat.find('d:duration', ns)
                    if duration:
                        duration_max = repeat.find('d:durationMax', ns)
                        if duration_max:
                            duration_value = duration.attrib['value'] + '-' + duration_max.attrib['value']
                        duration_unit = repeat.find('d:durationUnit', ns).attrib['value']
                        duration = duration_value + ' ' + duration_unit
                        medication_statement['dosage_duration'] = duration_value
                    frequency = repeat.find('d:frequency', ns)
                    if frequency:
                        medication_statement['dosage_frequency'] = frequency.attrib['value']
                    period = repeat.find('d:period', ns).attrib['value']
                    if period:
                        period_max = repeat.find('d:periodMax', ns)
                        if period_max:
                            period_value = period.attrib['value'] + '-' + period_max.attrib['value']
                        period_unit = repeat.find('d:periodUnit', ns)
                        period = period_value + ' ' + period_unit.attrib['value']
                        medication_statement['dosage_period'] = period
                    when = repeat.find('d:when', ns)
                    if when:
                        medication_statement['dosage_when'] = when.attrib['value']
                    offset = repeat.find('d:offset', ns)
                    if offset:
                        medication_statement['dosage_offset'] = offset.attrib['value']
            route = dosage.find('d:route', ns)
            if route:
                medication_statement['dosage_route'] = route.find(
                    'd:text', ns).attrib['value']
            dose_and_rate = dosage.find('d:doseAndRate', ns)
            if dose_and_rate:
                dose_quantity = dose_and_rate.find('d:doseQuantity', ns)
                quantity = dose_quantity.find('d:value', ns).attrib['value']
                unit = dose_quantity.find('d:unit', ns).attrib['value']
                medication_statement['dosage_quantity'] = quantity + ' ' + unit
    return medication_statement


def query_practitioner(practitioner_identifier, get_id):
    practitioner = {}
    get_practitioner = requests.get(fhir_server + '/Practitioner?identifier=urn:trinhcongminh|' +
                                    practitioner_identifier, headers={'Content-type': 'application/xml'})
    if get_practitioner.status_code == 200 and 'entry' in get_practitioner.content.decode('utf-8'):
        get_root = ET.fromstring(get_practitioner.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        practitioner_resource = resource.find('d:Practitioner', ns)
        if get_id == True:
            practitioner['id'] = practitioner_resource.find(
                'd:id', ns).attrib['value']
        practitioner['identifier'] = practitioner_identifier
        practitioner_name = practitioner_resource.find('d:name', ns)
        if practitioner_name:
            practitioner['name'] = practitioner_name.find(
                'd:family', ns).attrib['value'] + ' ' + practitioner_name.find('d:given', ns).attrib['value']
        practitioner_telecom = practitioner_resource.find('d:telecom', ns)
        if practitioner_telecom:
            practitioner['telecom'] = practitioner_telecom.find(
                'd:value', ns).attrib['value']
        practitioner_gender = practitioner_resource.find('d:gender', ns)
        if practitioner_gender:
            if practitioner_gender.attrib['value'] == 'male':
                practitioner['gender'] = 'Nam'
            else:
                practitioner['gender'] = 'Nữ'
        practitioner_birthdate = practitioner_resource.find('d:birthDate', ns)
        if practitioner_birthdate:
            practitioner['birthdate'] = practitioner_birthdate.attrib['value']
        practitioner_qualification = practitioner_resource.find(
            'd:qualification', ns)
        if practitioner_qualification:
            practitioner_qualification_code = practitioner_qualification.find(
                'd:code', ns)
            practitioner['qualification'] = practitioner_qualification_code.find(
                'd:text', ns).attrib['value']
    return practitioner


def query_diagnostic_report(diagnostic_report_identifier, get_id):
    diagnostic_report = {}
    get_diagnostic_report = requests.get(fhir_server + '/DiagnosticReport?identifier=urn:trinhcongminh|' + diagnostic_report_identifier, headers={'Content-type': 'application/xml'})
    if get_diagnostic_report.status_code == 200 and 'entry' in get_diagnostic_report.content.decode('utf-8'):
        get_root = ET.fromstring(get_diagnostic_report.content.decode('utf-8'))
        entry = get_root.find('d:entry', ns)
        resource = entry.find('d:resource', ns)
        diagnostic_report_resource = resource.find('d:DiagnosticReport', ns)
        if get_id == True:
            id_ = diagnostic_report_resource.find('d:id', ns)
            diagnostic_report['id'] = id_.attrib['value']
        diagnostic_report['diagnostic_identifier'] = diagnostic_report_identifier
        status = diagnostic_report_resource.find('d:status', ns)
        if status:
            diagnostic_report['diagnostic_status'] = status.attrib['value']
        category = diagnostic_report_resource.find('d:category', ns)
        if category:
            diagnostic_report['diagnostic_category'] = category.find('d:text', ns).attrib['value']
        
        code = diagnostic_report_resource.find('d:code', ns)
        if code:
            diagnostic_report['diagnostic_code'] = code.find('d:text', ns)
        effective = diagnostic_report_resource.find('d:effectiveDateTime', ns)
        if effective:
            diagnostic_report['diagnostic_effective'] = effective.attrib['value']
        conclusion = diagnostic_report_resource.find('d:conclusion', ns)
        if conclusion:
            diagnostic_report['diagnostic_conclusion'] = conclusion.attrib['value']
    return diagnostic_report