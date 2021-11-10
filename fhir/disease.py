import openpyxl as xl
from .models import DischargeDiseases, ComorbidityDiseases


#Get discharge diseases:
wb = xl.load_workbook('fhir/ICD-10.xlsx', data_only=True)
sh = wb['ICD10']
max_row = sh.max_row
for i in range(4, max_row + 1):
    name_cell = sh.cell(row=i, column=20)
    print(name_cell.value)
    code_cell = sh.cell(row=i, column=18)
    name = name_cell.value
    code = code_cell.value
    DischargeDiseases.objects.create(disease_code=code, disease_name=name, disease_search = name + ' ' + code)


#Get comorbidity diseases:
sh = wb['A1']
max_row = sh.max_row
diseases = {}
for i in range(4, max_row + 1):
    main_code = sh.cell(row=i, column=1)
    main_name = sh.cell(row=i, column=2)
    name_cell = sh.cell(row=i, column=6)
    if main_name.value != None:
        code_cell = sh.cell(row=i, column=3)
        name = name_cell.value
        code = code_cell.value
        if diseases.get(main_code.value):        
            diseases[main_code.value].append({'name': name, 'code': code})
        else:
            diseases[main_code.value] = []
            diseases[main_code.value].append({'name': name, 'code': code})
for key, value in diseases.items():
    try:
        main_disease = DischargeDiseases.objects.get(disease_code=key)
        for disease in value:
            ComorbidityDiseases.objects.create(discharge_diseases=main_disease, disease_code=disease['code'], disease_name=disease['name'], disease_search=disease['name'] + ' ' + disease['code'])
    except:
        pass


print('finished')