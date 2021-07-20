from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from lib.tools import generate_password
from .models import Encounter, ServiceRequest, Procedure, Allergy, UserModel

class EHRCreationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('full_name', 'gender', 'birth_date',
                  'home_address', 'work_address', 'user_identifier', 'telecom')

class Encounter(forms.ModelForm):
    class Meta:
        model = Encounter()
        fields = ('user_identifier', 'class_select', 'type_select',
         'service_type', 'priority', 'reason_code', 'location')

class UserForm(forms.ModelForm):
    class Meta:
        model = UserModel()
        fields = ('user_identifier', 'full_name', 'gender', 'birth_date', 'home_address', 'work_address', 'telecom')